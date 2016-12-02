from wikiwho.models import Article


def is_db_running():
    try:
        Article.objects.count()
    except:
        return False
    return True
