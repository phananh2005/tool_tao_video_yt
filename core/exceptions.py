"""Hệ thống ngoại lệ chuyên biệt cho TubeChain."""

class TubeChainException(Exception):
    """Ngoại lệ cơ sở cho toàn bộ ứng dụng TubeChain."""
    pass


class ImageGenerationError(TubeChainException):
    """Ngoại lệ chung trong quá trình sinh hình ảnh."""
    pass


class ImageRefusalError(ImageGenerationError):
    """Ngoại lệ khi AI từ chối tạo hình ảnh do bản quyền bên thứ ba hoặc chính sách nội dung."""
    def __init__(self, message: str = "", reason: str = "", prompt: str = ""):
        super().__init__(message)
        self.reason = reason
        self.prompt = prompt


class ImageTimeoutError(ImageGenerationError):
    """Ngoại lệ khi quá thời gian chờ AI phản hồi hoặc sinh ảnh."""
    pass
