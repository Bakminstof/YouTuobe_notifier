from asyncio import gather

from apps.notifier.schemas import ChannelModel, ContentType
from database.models import Stream, Video
from database.utils import get_stream_db, get_video_db
from utils.scrapper import get_content_urls


# ========================|Load last content URLs from database|======================== #
async def db_load_ch_content(channel_models: list[ChannelModel]) -> None:
    for ch_model in channel_models:
        await _db_load_ch_content(ch_model)


async def _db_load_ch_content(ch_model: ChannelModel) -> None:
    ch_model.db_videos = [video.url for video in await db_load_ch_videos(ch_model.id)]
    ch_model.db_streams = [stream.url for stream in await db_load_ch_streams(ch_model.id)]


async def db_load_ch_videos(channel_id: int) -> list[Video]:
    async with get_video_db() as video_db:
        videos = []
        load_options = {"channel_id": channel_id}

        async for videos_batch in video_db.aiter_load(video_db.get, **load_options):
            videos.extend(videos_batch)

        return videos


async def db_load_ch_streams(channel_id: int) -> list[Stream]:
    async with get_stream_db() as stream_db:
        streams = []
        load_options = {"channel_id": channel_id}

        async for streams_batch in stream_db.aiter_load(stream_db.get, **load_options):
            streams.extend(streams_batch)

        return streams


# ===========================|Load content URLs from YouTube|=========================== #
async def load_content_urls(channel_models: list[ChannelModel]) -> None:
    tasks = []

    for ch_model in channel_models:
        tasks.append(_load_content_urls(ch_model))

    await gather(*tasks)


async def _load_content_urls(ch_model: ChannelModel) -> None:
    tasks = [__load_videos_urls(ch_model), __load_streams_urls(ch_model)]
    await gather(*tasks)


async def __load_videos_urls(ch_model: ChannelModel) -> None:
    ch_model.loaded_videos = await get_content_urls(ch_model.url, ContentType.videos)


async def __load_streams_urls(ch_model: ChannelModel) -> None:
    ch_model.loaded_streams = await get_content_urls(ch_model.url, ContentType.streams)


# ==============================|Detect new content URLs|=============================== #
def check_new_content(channel_models: list[ChannelModel]) -> None:
    for ch_model in channel_models:
        _check_new_videos(ch_model)
        _check_new_streams(ch_model)


def _check_new_videos(ch_model: ChannelModel) -> None:
    new_videos = []

    for loaded_video in ch_model.loaded_videos:
        if loaded_video not in ch_model.db_videos:
            new_videos.append(loaded_video)

    if new_videos:
        ch_model.new_videos = new_videos


def _check_new_streams(ch_model: ChannelModel) -> None:
    new_streams = []

    for loaded_stream in ch_model.loaded_streams:
        if loaded_stream not in ch_model.db_streams:
            new_streams.append(loaded_stream)

    if new_streams:
        ch_model.new_streams = new_streams


# ===============================|Save new content URLs|================================ #
async def save_new_content(channel_models: list[ChannelModel]) -> None:
    for ch_model in channel_models:
        if ch_model.new_videos:
            await save_videos_urls(ch_model.id, ch_model.new_videos)

        if ch_model.new_streams:
            await save_streams_urls(ch_model.id, ch_model.new_streams)


async def save_videos_urls(
    channel_id: int,
    video_urls: list[str] | set[str],
) -> list[Video]:
    async with get_video_db() as video_db:
        videos = [Video(url=url, channel_id=channel_id) for url in video_urls]
        await video_db.create(videos)
        return videos


async def save_streams_urls(
    channel_id: int,
    stream_urls: list[str] | set[str],
) -> list[Stream]:
    async with get_stream_db() as stream_db:
        streams = [Stream(url=url, channel_id=channel_id) for url in stream_urls]
        await stream_db.create(streams)
        return streams
