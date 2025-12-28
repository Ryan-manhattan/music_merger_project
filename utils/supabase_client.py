# -*- coding: utf-8 -*-
"""
Supabase 클라이언트 모듈
PostgreSQL 기반 클라우드 데이터베이스 연동
"""
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils import app_settings
except ImportError:
    import app_settings

try:
    from supabase import create_client, Client
except ImportError:
    print("[WARN] supabase가 설치되지 않았습니다. 'pip install supabase'를 실행하세요.")
    Client = None
    create_client = None


class SupabaseClient:
    """
    Supabase 클라이언트
    커뮤니티 게시글을 PostgreSQL 데이터베이스에 저장
    """

    # visitor_logs 테이블이 없는 환경에서 에러 로그가 과도하게 쌓이는 것을 방지
    # (기능 자체가 핵심이 아니므로, 테이블 미존재 시 전체적으로 자동 비활성화)
    _visitor_logging_disabled_global = False
    
    def __init__(self, url: str = None, key: str = None):
        """
        초기화
        
        Args:
            url: Supabase 프로젝트 URL
            key: Supabase API 키 (anon key)
        """
        if Client is None or create_client is None:
            raise ImportError("supabase가 설치되지 않았습니다. 'pip install supabase'를 실행하세요.")
        
        self.url = url or app_settings.SUPABASE_URL
        self.key = key or app_settings.SUPABASE_KEY
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY가 설정되지 않았습니다.")
        
        # Supabase 클라이언트 초기화
        self.client: Client = create_client(self.url, self.key)

        # 인스턴스별 플래그는 두지 않고, 전역(class) 플래그를 사용
    
    def create_post(self, title: str, content: str, author: str = "Anonymous", user_id: str = None) -> Optional[str]:
        """
        게시글 생성
        
        Args:
            title: 제목
            content: 내용
            author: 작성자 (기본값: Anonymous)
            user_id: 사용자 ID (로그인한 경우)
        
        Returns:
            Optional[str]: 생성된 레코드 ID
        """
        try:
            data = {
                "title": title,
                "content": content,
                "author": author,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # user_id가 제공되면 추가
            if user_id:
                data["user_id"] = user_id
            
            response = self.client.table("posts").insert(data).execute()
            
            if response.data:
                record_id = response.data[0].get("id")
                print(f"[INFO] Supabase 게시글 생성 성공: {record_id}")
                return str(record_id)
            else:
                print("[ERROR] Supabase 게시글 생성 실패: 응답 데이터 없음")
                return None
                
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 생성 실패: {e}")
            return None
    
    def get_posts(self, limit: int = 50, offset: int = 0, user_id: str = None) -> List[Dict]:
        """
        게시글 목록 조회
        
        Args:
            limit: 조회 개수 제한
            offset: 오프셋
            user_id: 사용자 ID (필터링용, None이면 모든 사용자)
        
        Returns:
            List[Dict]: 게시글 리스트
        """
        try:
            query = self.client.table("posts").select("*")
            
            # user_id가 제공되면 필터링
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = (
                query
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 조회 실패: {e}")
            return []
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """
        게시글 상세 조회
        
        Args:
            post_id: 게시글 ID
        
        Returns:
            Optional[Dict]: 게시글 정보
        """
        try:
            response = (
                self.client.table("posts")
                .select("*")
                .eq("id", post_id)
                .single()
                .execute()
            )
            
            return response.data if response.data else None
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 조회 실패: {e}")
            return None
    
    def update_post(self, post_id: str, title: str = None, content: str = None) -> bool:
        """
        게시글 수정
        
        Args:
            post_id: 게시글 ID
            title: 제목 (선택)
            content: 내용 (선택)
        
        Returns:
            bool: 성공 여부
        """
        try:
            data = {
                "updated_at": datetime.now().isoformat()
            }
            
            if title:
                data["title"] = title
            if content:
                data["content"] = content
            
            response = (
                self.client.table("posts")
                .update(data)
                .eq("id", post_id)
                .execute()
            )
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 수정 실패: {e}")
            return False
    
    def delete_post(self, post_id: str) -> bool:
        """
        게시글 삭제
        
        Args:
            post_id: 게시글 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            response = (
                self.client.table("posts")
                .delete()
                .eq("id", post_id)
                .execute()
            )
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Supabase 게시글 삭제 실패: {e}")
            return False

    # =========================
    # Tracks (곡) + Comments (감상 코멘트)
    # =========================
    def get_tracks(self, limit: int = 50, offset: int = 0, user_id: str = None, playlist_id: str = None) -> List[Dict]:
        """곡 목록 조회 (display_order 우선, 그 다음 최신 등록 순, user_id, playlist_id로 필터링)"""
        try:
            query = self.client.table("tracks").select("*")
            
            # user_id가 제공되면 필터링
            if user_id:
                query = query.eq("user_id", user_id)
            
            # playlist_id가 제공되면 필터링 (None이면 플레이리스트 없는 곡만)
            if playlist_id is not None:
                if playlist_id == "":
                    # 빈 문자열이면 플레이리스트 없는 곡만
                    query = query.is_("playlist_id", "null")
                else:
                    query = query.eq("playlist_id", playlist_id)
            
            response = (
                query
                .order("display_order", desc=False)  # display_order 오름차순 우선
                .order("created_at", desc=True)  # 그 다음 최신 등록 순
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            print(f"[ERROR] Supabase tracks 조회 실패: {e}")
            return []

    def get_track(self, track_id: str) -> Optional[Dict]:
        """곡 상세 조회"""
        try:
            response = (
                self.client.table("tracks")
                .select("*")
                .eq("id", track_id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as e:
            print(f"[ERROR] Supabase track 조회 실패: {e}")
            return None

    def get_track_by_url(self, url: str, user_id: str = None, playlist_id: str = None) -> Optional[Dict]:
        """URL로 곡 조회 (user_id, playlist_id로 필터링, 중복 등록 방지)"""
        try:
            query = self.client.table("tracks").select("*").eq("url", url)
            
            # user_id가 제공되면 해당 사용자의 것만 조회
            if user_id:
                query = query.eq("user_id", user_id)
            
            # playlist_id가 제공되면 해당 플레이리스트의 것만 조회
            # playlist_id가 None이면 플레이리스트 없는 곡만 조회
            if playlist_id is not None:
                if playlist_id == "":
                    query = query.is_("playlist_id", "null")
                else:
                    query = query.eq("playlist_id", playlist_id)
            
            response = query.limit(1).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"[ERROR] Supabase track(url) 조회 실패: {e}")
            return None

    def create_track(
        self,
        url: str,
        source: str,
        title: str,
        artist: str = None,
        duration_seconds: int = None,
        thumbnail_url: str = None,
        source_id: str = None,
        metadata: Dict = None,
        user_id: str = None,
        playlist_id: str = None,
    ) -> Optional[str]:
        """곡 생성 (user_id, playlist_id 포함)"""
        try:
            data = {
                "url": url,
                "source": source,
                "source_id": source_id,
                "title": title,
                "artist": artist,
                "duration_seconds": duration_seconds,
                "thumbnail_url": thumbnail_url,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            
            # user_id가 제공되면 추가
            if user_id:
                data["user_id"] = user_id
            
            # playlist_id가 제공되면 추가
            if playlist_id:
                data["playlist_id"] = playlist_id
            
            response = self.client.table("tracks").insert(data).execute()
            if response.data:
                record_id = response.data[0].get("id")
                print(f"[INFO] Supabase tracks 생성 성공: {record_id} (user_id: {user_id}, playlist_id: {playlist_id})")
                return str(record_id)
            print("[ERROR] Supabase tracks 생성 실패: 응답 데이터 없음")
            return None
        except Exception as e:
            print(f"[ERROR] Supabase tracks 생성 실패: {e}")
            return None

    def create_track_comment(self, track_id: str, content: str, author: str = "Anonymous", user_id: str = None) -> Optional[str]:
        """곡 코멘트 생성 (user_id 포함)"""
        try:
            data = {
                "track_id": track_id,
                "content": content,
                "author": author,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            
            # user_id가 제공되면 추가
            if user_id:
                data["user_id"] = user_id
            
            response = self.client.table("track_comments").insert(data).execute()
            if response.data:
                record_id = response.data[0].get("id")
                print(f"[INFO] Supabase track_comments 생성 성공: {record_id} (user_id: {user_id})")
                return str(record_id)
            print("[ERROR] Supabase track_comments 생성 실패: 응답 데이터 없음")
            return None
        except Exception as e:
            print(f"[ERROR] Supabase track_comments 생성 실패: {e}")
            return None

    def get_track_comments(self, track_id: str, limit: int = 50, offset: int = 0, track_user_id: str = None, current_user_id: str = None) -> List[Dict]:
        """
        곡 코멘트 목록 (최신 순)
        
        Args:
            track_id: 트랙 ID
            limit: 조회 개수
            offset: 오프셋
            track_user_id: 트랙을 추가한 사용자 ID (본인 곡의 코멘트만 보이도록)
            current_user_id: 현재 로그인한 사용자 ID
        
        Returns:
            코멘트 목록 (본인이 추가한 곡이면 본인 코멘트만, 아니면 모든 코멘트)
        """
        try:
            query = self.client.table("track_comments").select("*").eq("track_id", track_id)
            
            # 본인이 추가한 곡인 경우: 본인이 작성한 코멘트만 조회
            if track_user_id and current_user_id and track_user_id == current_user_id:
                query = query.eq("user_id", current_user_id)
            
            response = (
                query
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            print(f"[ERROR] Supabase track_comments 조회 실패: {e}")
            return []

    def delete_track_comment(self, comment_id: str) -> bool:
        """곡 코멘트 삭제"""
        try:
            self.client.table("track_comments").delete().eq("id", comment_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase track_comments 삭제 실패: {e}")
            return False

    def update_track(self, track_id: str, data: Dict) -> bool:
        """곡 메타데이터/필드 업데이트"""
        try:
            if not data:
                return True
            data = dict(data)
            data["updated_at"] = datetime.now().isoformat()
            self.client.table("tracks").update(data).eq("id", track_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase tracks 업데이트 실패: {e}")
            return False
    
    def delete_track(self, track_id: str) -> bool:
        """곡 삭제"""
        try:
            self.client.table("tracks").delete().eq("id", track_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase tracks 삭제 실패: {e}")
            return False
    
    def get_random_tracks(self, count: int = 2, user_id: str = None, exclude_ids: List[str] = None) -> List[Dict]:
        """
        랜덤 곡 조회 (이상형 월드컵용)
        
        Args:
            count: 조회할 곡 개수
            user_id: 사용자 ID (해당 사용자의 곡만 조회)
            exclude_ids: 제외할 track ID 리스트
        
        Returns:
            List[Dict]: 랜덤 곡 리스트
        """
        try:
            query = self.client.table("tracks").select("*")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            if exclude_ids and len(exclude_ids) > 0:
                # Supabase Python 클라이언트는 not_.in_을 직접 지원하지 않으므로
                # 모든 결과를 가져온 후 필터링
                pass
            
            # 모든 곡 조회 후 랜덤 선택 (Supabase는 직접 랜덤 쿼리를 지원하지 않으므로)
            response = query.execute()
            all_tracks = response.data if response.data else []
            
            # exclude_ids 필터링
            if exclude_ids and len(exclude_ids) > 0:
                all_tracks = [t for t in all_tracks if t.get("id") not in exclude_ids]
            
            if len(all_tracks) < count:
                return all_tracks
            
            return random.sample(all_tracks, count)
        except Exception as e:
            print(f"[ERROR] Supabase 랜덤 tracks 조회 실패: {e}")
            return []
    
    def create_track_battle(self, user_id: str, track_a_id: str, track_b_id: str, winner_id: str) -> Optional[str]:
        """
        이상형 월드컵 투표 결과 저장
        
        Args:
            user_id: 사용자 ID
            track_a_id: 곡 A ID
            track_b_id: 곡 B ID
            winner_id: 선택한 곡 ID
        
        Returns:
            Optional[str]: 생성된 레코드 ID
        """
        try:
            data = {
                "user_id": user_id,
                "track_a_id": track_a_id,
                "track_b_id": track_b_id,
                "winner_id": winner_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.client.table("track_battles").insert(data).execute()
            if response.data:
                record_id = response.data[0].get("id")
                print(f"[INFO] Supabase track_battles 생성 성공: {record_id}")
                return str(record_id)
            return None
        except Exception as e:
            print(f"[ERROR] Supabase track_battles 생성 실패: {e}")
            return None
    
    def get_track_battle_stats(self, track_id: str) -> Dict:
        """
        곡의 이상형 월드컵 통계 조회
        
        Args:
            track_id: 곡 ID
        
        Returns:
            Dict: {wins: int, total_battles: int, win_rate: float}
        """
        try:
            # 승리한 횟수
            wins_response = (
                self.client.table("track_battles")
                .select("id", count="exact")
                .eq("winner_id", track_id)
                .execute()
            )
            wins = wins_response.count if wins_response.count else 0
            
            # 참여한 총 배틀 수 (track_a_id 또는 track_b_id로 참여)
            total_a_response = (
                self.client.table("track_battles")
                .select("id", count="exact")
                .eq("track_a_id", track_id)
                .execute()
            )
            total_b_response = (
                self.client.table("track_battles")
                .select("id", count="exact")
                .eq("track_b_id", track_id)
                .execute()
            )
            
            total_a = total_a_response.count if total_a_response.count else 0
            total_b = total_b_response.count if total_b_response.count else 0
            total = total_a + total_b
            
            win_rate = (wins / total * 100) if total > 0 else 0.0
            
            return {
                "wins": wins,
                "total_battles": total,
                "win_rate": round(win_rate, 1)
            }
        except Exception as e:
            print(f"[ERROR] Supabase track_battles 통계 조회 실패: {e}")
            return {"wins": 0, "total_battles": 0, "win_rate": 0.0}
    
    def get_worldcup_rankings(self, limit: int = 50) -> List[Dict]:
        """
        이상형 월드컵 투표 결과 순위 조회 (승리 횟수 기준)
        
        Args:
            limit: 조회할 최대 순위 수
        
        Returns:
            List[Dict]: 순위별 곡 정보 리스트 (승리 횟수 내림차순)
        """
        try:
            # 모든 투표에서 승리한 곡들의 승리 횟수 집계
            response = (
                self.client.table("track_battles")
                .select("winner_id")
                .execute()
            )
            
            # 승리 횟수 집계
            win_counts = {}
            for battle in response.data:
                winner_id = battle.get("winner_id")
                if winner_id:
                    win_counts[winner_id] = win_counts.get(winner_id, 0) + 1
            
            # 승리 횟수로 정렬
            sorted_tracks = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)
            
            # 상위 limit개만 선택
            top_tracks = sorted_tracks[:limit]
            
            # 곡 정보와 함께 반환
            rankings = []
            for rank, (track_id, wins) in enumerate(top_tracks, 1):
                # 곡 정보 조회
                track_response = (
                    self.client.table("tracks")
                    .select("*")
                    .eq("id", track_id)
                    .execute()
                )
                
                if track_response.data:
                    track = track_response.data[0]
                    rankings.append({
                        "rank": rank,
                        "track_id": track_id,
                        "wins": wins,
                        "title": track.get("title", "Unknown"),
                        "artist": track.get("artist", "Unknown"),
                        "cover_url": track.get("cover_url"),
                        "source_url": track.get("source_url"),
                        "duration_seconds": track.get("duration_seconds", 0)
                    })
            
            return rankings
        except Exception as e:
            print(f"[ERROR] Supabase 월드컵 순위 조회 실패: {e}")
            return []
    
    def get_worldcup_stats(self) -> Dict:
        """
        월드컵 투표 통계 조회
        
        Returns:
            Dict: {total_battles: int, total_votes: int, recent_battles: int}
        """
        try:
            # 전체 배틀 수 (투표 수)
            battles_response = (
                self.client.table("track_battles")
                .select("id", count="exact")
                .execute()
            )
            total_battles = battles_response.count if battles_response.count else 0
            
            # 최근 7일간의 배틀 수
            from datetime import datetime, timedelta
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            recent_response = (
                self.client.table("track_battles")
                .select("id", count="exact")
                .gte("created_at", seven_days_ago)
                .execute()
            )
            recent_battles = recent_response.count if recent_response.count else 0
            
            return {
                "total_battles": total_battles,
                "total_votes": total_battles,  # 배틀 수 = 투표 수
                "recent_battles": recent_battles
            }
        except Exception as e:
            print(f"[ERROR] Supabase 월드컵 통계 조회 실패: {e}")
            return {"total_battles": 0, "total_votes": 0, "recent_battles": 0}
    
    def get_today_visits(self) -> int:
        """
        오늘 방문횟수 조회
        
        Returns:
            int: 오늘 방문횟수
        """
        try:
            from datetime import datetime, timedelta
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_iso = today_start.isoformat()
            
            response = (
                self.client.table("visitor_logs")
                .select("id", count="exact")
                .gte("visited_at", today_start_iso)
                .execute()
            )
            
            return response.count if response.count else 0
        except Exception as e:
            print(f"[ERROR] Supabase 오늘 방문횟수 조회 실패: {e}")
            return 0
    
    # =========================
    # Playlists (플레이리스트)
    # =========================
    def create_playlist(self, name: str, description: str = None, user_id: str = None) -> Optional[str]:
        """
        플레이리스트 생성
        
        Args:
            name: 플레이리스트 이름
            description: 설명 (선택)
            user_id: 사용자 ID
        
        Returns:
            Optional[str]: 생성된 플레이리스트 ID
        """
        try:
            if not user_id:
                return None
            
            data = {
                "name": name,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            if description:
                data["description"] = description
            
            response = self.client.table("playlists").insert(data).execute()
            if response.data:
                record_id = response.data[0].get("id")
                print(f"[INFO] Supabase playlists 생성 성공: {record_id}")
                return str(record_id)
            return None
        except Exception as e:
            print(f"[ERROR] Supabase playlists 생성 실패: {e}")
            return None
    
    def get_playlists(self, user_id: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        플레이리스트 목록 조회
        
        Args:
            user_id: 사용자 ID (해당 사용자의 플레이리스트만 조회)
            limit: 조회 개수
            offset: 오프셋
        
        Returns:
            List[Dict]: 플레이리스트 리스트
        """
        try:
            query = self.client.table("playlists").select("*")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = (
                query
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            print(f"[ERROR] Supabase playlists 조회 실패: {e}")
            return []
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """
        플레이리스트 상세 조회
        
        Args:
            playlist_id: 플레이리스트 ID
        
        Returns:
            Optional[Dict]: 플레이리스트 정보
        """
        try:
            response = (
                self.client.table("playlists")
                .select("*")
                .eq("id", playlist_id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as e:
            print(f"[ERROR] Supabase playlist 조회 실패: {e}")
            return None
    
    def update_playlist(self, playlist_id: str, name: str = None, description: str = None, icon_url: str = None) -> bool:
        """
        플레이리스트 수정
        
        Args:
            playlist_id: 플레이리스트 ID
            name: 이름 (선택)
            description: 설명 (선택)
            icon_url: 아이콘 이미지 URL (선택)
        
        Returns:
            bool: 성공 여부
        """
        try:
            data = {
                "updated_at": datetime.now().isoformat()
            }
            
            if name:
                data["name"] = name
            if description is not None:
                data["description"] = description
            if icon_url is not None:
                data["icon_url"] = icon_url
            
            self.client.table("playlists").update(data).eq("id", playlist_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase playlist 수정 실패: {e}")
            return False
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        플레이리스트 삭제
        
        Args:
            playlist_id: 플레이리스트 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            self.client.table("playlists").delete().eq("id", playlist_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase playlist 삭제 실패: {e}")
            return False
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        플레이리스트의 곡 목록 조회
        
        Args:
            playlist_id: 플레이리스트 ID
            limit: 조회 개수
            offset: 오프셋
        
        Returns:
            List[Dict]: 곡 리스트
        """
        try:
            response = (
                self.client.table("tracks")
                .select("*")
                .eq("playlist_id", playlist_id)
                .order("display_order", desc=False)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            print(f"[ERROR] Supabase playlist tracks 조회 실패: {e}")
            return []
    
    def update_tracks_order(self, track_orders: List[Dict]) -> bool:
        """
        여러 곡의 순서를 한 번에 업데이트
        
        Args:
            track_orders: [{"id": track_id, "order": order_value}, ...] 형태의 리스트
        
        Returns:
            bool: 성공 여부
        """
        try:
            for item in track_orders:
                track_id = item.get("id")
                order_value = item.get("order")
                if track_id and order_value is not None:
                    self.client.table("tracks").update({
                        "display_order": order_value,
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", track_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Supabase tracks 순서 업데이트 실패: {e}")
            return False
    
    def log_visitor(self, ip_address: str, user_agent: str, page_url: str, referer: str = None) -> bool:
        """
        방문자 로그 기록
        
        Args:
            ip_address: 방문자 IP 주소
            user_agent: 브라우저/디바이스 정보
            page_url: 방문한 페이지 URL
            referer: 이전 페이지 URL (선택)
        
        Returns:
            bool: 성공 여부
        """
        try:
            if SupabaseClient._visitor_logging_disabled_global:
                return False

            data = {
                "ip_address": ip_address,
                "user_agent": user_agent[:500] if user_agent else None,  # 길이 제한
                "page_url": page_url[:500] if page_url else None,
                "referer": referer[:500] if referer else None,
                "visited_at": datetime.now().isoformat()
            }
            
            response = self.client.table("visitor_logs").insert(data).execute()
            
            if response.data:
                print(f"[INFO] 방문자 로그 기록 성공: {ip_address} - {page_url}")
                return True
            else:
                print("[ERROR] 방문자 로그 기록 실패: 응답 데이터 없음")
                return False
                
        except Exception as e:
            # 로그 기록 실패해도 앱은 계속 동작해야 함
            # visitor_logs 테이블이 없는 경우(PGRST205)에는 반복 로그를 막기 위해 비활성화
            err0 = e.args[0] if getattr(e, "args", None) else None
            if isinstance(err0, dict):
                code = err0.get("code")
                message = err0.get("message", "")
            else:
                code = None
                message = str(e)

            if code == "PGRST205" and "visitor_logs" in message:
                SupabaseClient._visitor_logging_disabled_global = True
                print("[WARN] visitor_logs 테이블이 없어 방문자 로그를 비활성화합니다.")
                return False

            print(f"[ERROR] 방문자 로그 기록 실패: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Supabase 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            # 간단한 쿼리로 연결 테스트
            response = self.client.table("posts").select("id").limit(1).execute()
            print("[INFO] Supabase 연결 성공!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Supabase 연결 실패: {e}")
            return False


def main():
    """테스트용 메인 함수"""
    try:
        client = SupabaseClient()
        print("=== Supabase 연결 테스트 ===")
        print()
        
        # 연결 테스트
        if client.test_connection():
            print("✓ 연결 성공!")
        else:
            print("✗ 연결 실패")
            
    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

