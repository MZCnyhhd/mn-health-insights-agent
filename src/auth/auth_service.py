import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import datetime
import time
import re

class AuthService:
    """处理所有与Supabase认证和数据交互相关的服务"""
    def __init__(self):
        """初始化AuthService，建立与Supabase的连接"""
        try:
            # 自定义连接参数
            self.supabase = st.connection(
                "supabase",
                type=SupabaseConnection,
                ttl=None,  # 禁用缓存
                url=st.secrets["SUPABASE_URL"],  # 从secrets获取Supabase URL
                key=st.secrets["SUPABASE_KEY"],  # 从secrets获取Supabase key
                client_options={
                    "timeout": 60,  # 60秒超时
                    "retries": 3,   # 3次重试
                }
            )
        except Exception as e:
            st.error(f"服务初始化失败: {str(e)}")
            raise e
        
        # 如果没有当前会话，则尝试从Supabase恢复会话
        self.try_restore_session()
        
        # 初始化时验证会话
        if 'auth_token' in st.session_state:
            if not self.validate_session_token():
                self.sign_out()
    
    def try_restore_session(self):
        """尝试从Supabase存储的会话中恢复会话"""
        try:
            # 检查Supabase是否有存储的会话
            session = self.supabase.client.auth.get_session()
            if session and session.access_token and 'auth_token' not in st.session_state:
                # 验证存储的会话
                user = self.supabase.client.auth.get_user()
                if user and user.user:
                    user_data = self.get_user_data(user.user.id)
                    if user_data:
                        # 恢复会话状态
                        st.session_state.auth_token = session.access_token
                        st.session_state.user = user_data
        except Exception:
            # 如果恢复失败，则在没有会话的情况下继续
            pass

    def validate_email(self, email):
        """验证电子邮件格式"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    def check_existing_user(self, email):
        """检查用户是否已存在"""
        try:
            result = self.supabase.table('users')\
                .select('id')\
                .eq('email', email)\
                .execute()
            return len(result.data) > 0
        except Exception:
            return False

    def sign_up(self, email, password, name):
        """处理用户注册"""
        try:
            auth_response = self.supabase.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name
                    }
                }
            })
            
            if not auth_response.user:
                return False, "创建用户帐户失败"
            
            user_data = {
                'id': auth_response.user.id,
                'email': email,
                'name': name,
                'created_at': datetime.now().isoformat()
            }
            
            # 将用户数据插入users表
            self.supabase.table('users').insert(user_data).execute()
            
            return True, user_data
                
        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "already registered" in error_msg:
                return False, "电子邮件已注册"
            return False, f"注册失败: {str(e)}"

    def sign_in(self, email, password):
        """处理用户登录"""
        try:
            # 首先清除任何现有的会话数据
            self.sign_out()
            
            auth_response = self.supabase.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response and auth_response.user:
                # 获取用户数据
                user_data = self.get_user_data(auth_response.user.id)
                if not user_data:
                    return False, "未找到用户数据"
                    
                # 存储会话信息
                st.session_state.auth_token = auth_response.session.access_token
                st.session_state.user = user_data
                return True, user_data
                
            return False, "无效的登录响应"
        except Exception as e:
            return False, str(e)
    
    def sign_out(self):
        """退出并清除所有会话数据"""
        try:
            self.supabase.client.auth.sign_out()
            from auth.session_manager import SessionManager
            SessionManager.clear_session_state()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_user(self):
        """获取当前用户"""
        try:
            return self.supabase.client.auth.get_user()
        except Exception:
            return None

    def create_session(self, user_id, title=None):
        """创建新的聊天会话"""
        try:
            current_time = datetime.now()
            default_title = f"{current_time.strftime('%Y-%m-%d / %H:%M:%S')}"
            
            session_data = {
                'user_id': user_id,
                'title': title or default_title,
                'created_at': current_time.isoformat()
            }
            result = self.supabase.table('chat_sessions').insert(session_data).execute()
            return True, result.data[0] if result.data else None
        except Exception as e:
            return False, str(e)

    def get_user_sessions(self, user_id):
        """获取用户的聊天会话"""
        try:
            result = self.supabase.table('chat_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            return True, result.data
        except Exception as e:
            st.error(f"获取会话时出错: {str(e)}")
            return False, []

    def save_chat_message(self, session_id, content, role='user'):
        """保存聊天消息"""
        try:
            message_data = {
                'session_id': session_id,
                'content': content,
                'role': role,
                'created_at': datetime.now().isoformat()
            }
            result = self.supabase.table('chat_messages').insert(message_data).execute()
            return True, result.data[0] if result.data else None
        except Exception as e:
            return False, str(e)

    def get_session_messages(self, session_id):
        """获取会话的所有消息"""
        try:
            result = self.supabase.table('chat_messages')\
                .select('*')\
                .eq('session_id', session_id)\
                .order('created_at')\
                .execute()
            return True, result.data
        except Exception as e:
            return False, str(e)

    def delete_session(self, session_id):
        """删除一个聊天会话及其所有消息"""
        try:
            # 删除会话中的所有消息
            self.supabase.table('chat_messages')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()

            # 删除会话本身
            self.supabase.table('chat_sessions')\
                .delete()\
                .eq('id', session_id)\
                .execute()

            return True, None
        except Exception as e:
            st.error(f"删除会话失败: {str(e)}")
            return False, str(e)
    
    def validate_session_token(self):
        """在启动时验证现有的会话令牌"""
        try:
            session = self.supabase.client.auth.get_session()
            if not session or not session.access_token:
                return None
                
            # 验证令牌是否与存储的令牌匹配
            if session.access_token != st.session_state.get('auth_token'):
                return None
                
            user = self.supabase.client.auth.get_user()
            if not user or not user.user:
                return None
                
            return self.get_user_data(user.user.id)
        except Exception:
            return None
    
    def get_user_data(self, user_id):
        """从数据库获取用户数据"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .eq('id', user_id)\
                .single()\
                .execute()
            return response.data if response else None
        except Exception:
            return None
