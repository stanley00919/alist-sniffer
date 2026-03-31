import sys


def notify(title: str, message: str) -> None:
    """Show a Windows 10/11 toast notification. Fails silently on error."""
    if sys.platform != 'win32':
        return
    try:
        from winotify import Notification, audio
        toast = Notification(
            app_id='WebMedia Sniffer',
            title=title,
            msg=message,
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except Exception:
        pass
