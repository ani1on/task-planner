import ctypes
import os
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_void_p,
    create_string_buffer,
    wintypes,
)


class SessionStoreError(RuntimeError):
    """Raised when the operating-system credential store is unavailable."""


class _Credential(Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", c_void_p),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class SessionStore:
    TARGET_NAME = "Task Planner"
    USER_NAME = "refresh-token"
    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    ERROR_NOT_FOUND = 1168

    @staticmethod
    def _keyring():
        try:
            import keyring
        except ImportError as error:
            raise SessionStoreError(
                "Установите защищённое хранилище учётных данных для этой системы."
            ) from error
        return keyring

    @staticmethod
    def _credential_api():
        if os.name != "nt":
            raise SessionStoreError("Для этой системы нет Credential Manager.")

        advapi32 = ctypes.WinDLL("Advapi32", use_last_error=True)
        advapi32.CredWriteW.argtypes = [POINTER(_Credential), wintypes.DWORD]
        advapi32.CredWriteW.restype = wintypes.BOOL
        advapi32.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            POINTER(POINTER(_Credential)),
        ]
        advapi32.CredReadW.restype = wintypes.BOOL
        advapi32.CredDeleteW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        advapi32.CredDeleteW.restype = wintypes.BOOL
        advapi32.CredFree.argtypes = [c_void_p]
        advapi32.CredFree.restype = None
        return advapi32

    def load_refresh_token(self) -> str | None:
        if os.name != "nt":
            keyring = self._keyring()
            try:
                return keyring.get_password(self.TARGET_NAME, self.USER_NAME)
            except keyring.errors.KeyringError as error:
                raise SessionStoreError(
                    "Не удалось прочитать сохранённую сессию из защищённого хранилища."
                ) from error

        advapi32 = self._credential_api()
        credential = POINTER(_Credential)()
        if not advapi32.CredReadW(
            self.TARGET_NAME,
            self.CRED_TYPE_GENERIC,
            0,
            byref(credential),
        ):
            error_code = ctypes.get_last_error()
            if error_code == self.ERROR_NOT_FOUND:
                return None
            raise SessionStoreError(
                "Не удалось прочитать сохранённую сессию из Windows."
            ) from ctypes.WinError(error_code)

        try:
            data = ctypes.string_at(
                credential.contents.CredentialBlob,
                credential.contents.CredentialBlobSize,
            )
            return data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SessionStoreError(
                "Сохранённая сессия повреждена."
            ) from error
        finally:
            advapi32.CredFree(credential)

    def save_refresh_token(self, token: str):
        if os.name != "nt":
            keyring = self._keyring()
            try:
                keyring.set_password(self.TARGET_NAME, self.USER_NAME, token)
            except keyring.errors.KeyringError as error:
                raise SessionStoreError(
                    "Не удалось сохранить сессию в защищённом хранилище."
                ) from error
            return

        advapi32 = self._credential_api()
        encoded = token.encode("utf-8")
        buffer = create_string_buffer(encoded)
        credential = _Credential()
        credential.Type = self.CRED_TYPE_GENERIC
        credential.TargetName = self.TARGET_NAME
        credential.CredentialBlobSize = len(encoded)
        credential.CredentialBlob = ctypes.cast(buffer, c_void_p)
        credential.Persist = self.CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = self.USER_NAME

        if not advapi32.CredWriteW(byref(credential), 0):
            error_code = ctypes.get_last_error()
            raise SessionStoreError(
                "Не удалось сохранить сессию в Windows Credential Manager."
            ) from ctypes.WinError(error_code)

    def clear(self):
        if os.name != "nt":
            keyring = self._keyring()
            try:
                keyring.delete_password(self.TARGET_NAME, self.USER_NAME)
            except keyring.errors.PasswordDeleteError:
                return
            except keyring.errors.KeyringError as error:
                raise SessionStoreError(
                    "Не удалось удалить сессию из защищённого хранилища."
                ) from error
            return

        advapi32 = self._credential_api()
        if not advapi32.CredDeleteW(
            self.TARGET_NAME,
            self.CRED_TYPE_GENERIC,
            0,
        ):
            error_code = ctypes.get_last_error()
            if error_code != self.ERROR_NOT_FOUND:
                raise SessionStoreError(
                    "Не удалось удалить сохранённую сессию из Windows."
                ) from ctypes.WinError(error_code)
