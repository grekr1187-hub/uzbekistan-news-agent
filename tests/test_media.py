from pathlib import Path

from news_agent.video import make_news_image


def test_make_news_image_creates_vertical_jpeg(tmp_path: Path):
    output = tmp_path / "news.jpg"

    result = make_news_image(
        "Президент Узбекистана обсудил стратегическое партнёрство с США",
        "Встреча состоялась 3 сентября.",
        str(output),
    )

    assert result == str(output)
    assert output.exists()

    from PIL import Image

    with Image.open(output) as image:
        assert image.format == "JPEG"
        assert image.size == (1080, 1350)
