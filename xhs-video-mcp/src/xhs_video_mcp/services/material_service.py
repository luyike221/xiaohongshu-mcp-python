"""素材服务 - 搜索和下载视频素材"""
import os
import random
import hashlib
from typing import List
from urllib.parse import urlencode
from loguru import logger
import requests
from moviepy.video.io.VideoFileClip import VideoFileClip

from ..config import settings
from ..models.schema import MaterialInfo, VideoAspect


class MaterialService:
    """素材服务，用于搜索和下载视频素材"""
    
    def __init__(self):
        self.requested_count = 0
    
    def _get_api_key(self, cfg_key: str) -> str:
        """获取API Key（支持多个key轮询）"""
        api_keys = getattr(settings, cfg_key, None)
        if not api_keys:
            raise ValueError(f"{cfg_key} is not set in settings. Please set it in .env file.")
        
        def clean_key(key: str) -> str:
            """清理API key：去除前后空格和方括号"""
            if not isinstance(key, str):
                return str(key).strip()
            # 去除前后空格
            key = key.strip()
            # 去除方括号（如果存在）
            if key.startswith('[') and key.endswith(']'):
                key = key[1:-1].strip()
            # 去除引号（如果存在）
            if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
                key = key[1:-1].strip()
            return key
        
        if isinstance(api_keys, str):
            cleaned_key = clean_key(api_keys)
            if not cleaned_key:
                raise ValueError(f"{cfg_key} is empty after cleaning")
            return cleaned_key
        
        if isinstance(api_keys, list):
            if not api_keys:
                raise ValueError(f"{cfg_key} is empty in settings")
            # 清理所有key
            cleaned_keys = [clean_key(key) for key in api_keys if clean_key(key)]
            if not cleaned_keys:
                raise ValueError(f"{cfg_key} contains no valid keys after cleaning")
            # 多个key轮询使用
            self.requested_count += 1
            selected_key = cleaned_keys[self.requested_count % len(cleaned_keys)]
            logger.debug(f"Using {cfg_key} #{self.requested_count % len(cleaned_keys) + 1}/{len(cleaned_keys)}")
            return selected_key
        
        raise ValueError(f"Invalid {cfg_key} format in settings: {type(api_keys)}")
    
    def search_videos_pexels(
        self,
        search_term: str,
        minimum_duration: int,
        video_aspect: VideoAspect = VideoAspect.portrait,
    ) -> List[MaterialInfo]:
        """
        从Pexels搜索视频
        
        Args:
            search_term: 搜索关键词
            minimum_duration: 最小时长（秒）
            video_aspect: 视频比例
            
        Returns:
            素材信息列表
        """
        aspect = VideoAspect(video_aspect)
        video_width, video_height = aspect.to_resolution()
        video_orientation = "portrait" if aspect == VideoAspect.portrait else "landscape"
        
        try:
            api_key = self._get_api_key("pexels_api_keys")
            # 显示部分 API key 用于调试（隐藏中间部分）
            if api_key and len(api_key) > 8:
                masked_key = f"{api_key[:4]}...{api_key[-4:]}"
                logger.debug(f"Using Pexels API key: {masked_key}")
        except ValueError as e:
            logger.error(f"Pexels API key error: {e}")
            return []
        
        headers = {
            "Authorization": api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        params = {
            "query": search_term,
            "per_page": 20,
            "orientation": video_orientation
        }
        query_url = f"https://api.pexels.com/videos/search?{urlencode(params)}"
        
        logger.info(f"Searching Pexels videos: {query_url}")
        
        try:
            r = requests.get(
                query_url,
                headers=headers,
                proxies=settings.proxy,
                timeout=(30, 60)
            )
            
            # 检查 HTTP 状态码
            if r.status_code == 401:
                logger.error(f"Pexels API authentication failed (401 Unauthorized). "
                           f"Please check your API key. Status: {r.status_code}")
                logger.debug(f"Response: {r.text[:200]}")
                return []
            
            response = r.json()
            
            video_items = []
            if "videos" not in response:
                logger.error(f"Pexels search failed: {response}")
                logger.debug(f"HTTP Status: {r.status_code}, Response: {r.text[:500]}")
                return video_items
            
            videos = response["videos"]
            for v in videos:
                duration = v["duration"]
                if duration < minimum_duration:
                    continue
                
                video_files = v["video_files"]
                for video in video_files:
                    w = int(video["width"])
                    h = int(video["height"])
                    if w == video_width and h == video_height:
                        item = MaterialInfo(
                            provider="pexels",
                            url=video["link"],
                            duration=duration
                        )
                        video_items.append(item)
                        break
            
            logger.info(f"Found {len(video_items)} videos from Pexels")
            return video_items
        
        except Exception as e:
            logger.error(f"Failed to search Pexels videos: {e}")
            return []
    
    def search_videos_pixabay(
        self,
        search_term: str,
        minimum_duration: int,
        video_aspect: VideoAspect = VideoAspect.portrait,
    ) -> List[MaterialInfo]:
        """
        从Pixabay搜索视频
        
        Args:
            search_term: 搜索关键词
            minimum_duration: 最小时长（秒）
            video_aspect: 视频比例
            
        Returns:
            素材信息列表
        """
        aspect = VideoAspect(video_aspect)
        video_width, video_height = aspect.to_resolution()
        
        try:
            api_key = self._get_api_key("pixabay_api_keys")
        except ValueError:
            logger.error("Pixabay API key is not set")
            return []
        
        params = {
            "q": search_term,
            "video_type": "all",
            "per_page": 50,
            "key": api_key
        }
        query_url = f"https://pixabay.com/api/videos/?{urlencode(params)}"
        
        logger.info(f"Searching Pixabay videos: {query_url}")
        
        try:
            r = requests.get(
                query_url,
                proxies=settings.proxy,
                timeout=(30, 60)
            )
            response = r.json()
            
            video_items = []
            if "hits" not in response:
                logger.error(f"Pixabay search failed: {response}")
                return video_items
            
            videos = response["hits"]
            for v in videos:
                duration = v["duration"]
                if duration < minimum_duration:
                    continue
                
                video_files = v["videos"]
                for video_type in video_files:
                    video = video_files[video_type]
                    w = int(video["width"])
                    if w >= video_width:
                        item = MaterialInfo(
                            provider="pixabay",
                            url=video["url"],
                            duration=duration
                        )
                        video_items.append(item)
                        break
            
            logger.info(f"Found {len(video_items)} videos from Pixabay")
            return video_items
        
        except Exception as e:
            logger.error(f"Failed to search Pixabay videos: {e}")
            return []
    
    def save_video(self, video_url: str, save_dir: str = "") -> str:
        """
        下载并保存视频
        
        Args:
            video_url: 视频URL
            save_dir: 保存目录
            
        Returns:
            保存的视频文件路径，失败返回空字符串
        """
        if not save_dir:
            save_dir = settings.material_cache_dir
        
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件路径（基于URL的hash）
        url_without_query = video_url.split("?")[0]
        url_hash = hashlib.md5(url_without_query.encode()).hexdigest()
        video_id = f"vid-{url_hash}"
        video_path = os.path.join(save_dir, f"{video_id}.mp4")
        
        # 如果文件已存在，直接返回
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            logger.info(f"Video already exists: {video_path}")
            return video_path
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        logger.info(f"Downloading video: {video_url}")
        
        try:
            with open(video_path, "wb") as f:
                response = requests.get(
                    video_url,
                    headers=headers,
                    proxies=settings.proxy,
                    timeout=(60, 240),
                    stream=True
                )
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 验证视频文件
            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                try:
                    clip = VideoFileClip(video_path)
                    duration = clip.duration
                    fps = clip.fps
                    clip.close()
                    if duration > 0 and fps > 0:
                        logger.success(f"Video saved: {video_path}")
                        return video_path
                except Exception as e:
                    logger.warning(f"Invalid video file: {video_path}, error: {e}")
                    try:
                        os.remove(video_path)
                    except:
                        pass
            
            return ""
        
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except:
                pass
            return ""
    
    def download_videos(
        self,
        search_terms: List[str],
        source: str = "pexels",
        video_aspect: VideoAspect = VideoAspect.portrait,
        video_concat_mode: str = "random",
        audio_duration: float = 0.0,
        max_clip_duration: int = 5,
    ) -> List[str]:
        """
        下载视频素材
        
        Args:
            search_terms: 搜索关键词列表
            source: 素材来源（pexels或pixabay）
            video_aspect: 视频比例
            video_concat_mode: 拼接模式
            audio_duration: 音频时长（秒）
            max_clip_duration: 最大片段时长（秒）
            
        Returns:
            下载的视频文件路径列表
        """
        valid_video_items = []
        valid_video_urls = []
        found_duration = 0.0
        
        search_func = self.search_videos_pexels if source == "pexels" else self.search_videos_pixabay
        
        # 搜索视频
        for search_term in search_terms:
            video_items = search_func(
                search_term=search_term,
                minimum_duration=max_clip_duration,
                video_aspect=video_aspect,
            )
            
            logger.info(f"Found {len(video_items)} videos for '{search_term}'")
            
            for item in video_items:
                if item.url not in valid_video_urls:
                    valid_video_items.append(item)
                    valid_video_urls.append(item.url)
                    found_duration += item.duration
        
        logger.info(
            f"Total videos found: {len(valid_video_items)}, "
            f"required duration: {audio_duration}s, "
            f"found duration: {found_duration}s"
        )
        
        # 随机打乱（如果需要）
        if video_concat_mode == "random":
            random.shuffle(valid_video_items)
        
        # 下载视频
        video_paths = []
        total_duration = 0.0
        
        for item in valid_video_items:
            if total_duration > audio_duration:
                logger.info(f"Enough videos downloaded, total duration: {total_duration}s")
                break
            
            try:
                saved_video_path = self.save_video(video_url=item.url)
                if saved_video_path:
                    video_paths.append(saved_video_path)
                    seconds = min(max_clip_duration, item.duration)
                    total_duration += seconds
                    logger.info(f"Downloaded video: {saved_video_path}, duration: {seconds}s")
            except Exception as e:
                logger.error(f"Failed to download video: {item.url}, error: {e}")
        
        logger.success(f"Downloaded {len(video_paths)} videos")
        return video_paths

