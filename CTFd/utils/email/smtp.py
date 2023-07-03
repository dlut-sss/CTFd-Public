from CTFd.utils.email.providers.smtp import SMTPEmailProvider


def sendmail(addr, text, subject):
    print(
        "CTFd.utils.email.smtp.sendmail 将在 CTFd 的未来次要版本中引发异常，然后在 CTFd v4.0 中删除"
    )
    return SMTPEmailProvider.sendmail(addr, text, subject)
