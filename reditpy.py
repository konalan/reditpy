import praw
from dotenv import load_dotenv
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit


class RedditResultsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Résultats Reddit")
        self.setGeometry(100, 100, 800, 600)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

    def display_results(self, results):
        self.text_edit.setPlainText("\n".join(results))


def get_user_data(reddit, username):
    """
    Récupérer les données de l'utilisateur spécifié sur Reddit en utilisant l'API PRAW.
    Retourne un dictionnaire avec les informations de l'utilisateur.
    """
    user_data = {}

    try:
        redditor = reddit.redditor(username)
        user_data['karma_total'] = redditor.link_karma + redditor.comment_karma
        # Ajoutez d'autres informations de l'utilisateur que vous souhaitez récupérer dans le dictionnaire
        user_data['post_link'] = get_latest_post_link(redditor)
    except Exception as e:
        print("Erreur lors de la récupération des données de l'utilisateur", username)
        print("Message d'erreur :", str(e))

    return user_data


def get_latest_post_link(redditor):
    """
    Récupérer le lien du dernier post de l'utilisateur sur Reddit.
    """
    try:
        posts = redditor.submissions.new(limit=1)
        for post in posts:
            return f"https://www.reddit.com{post.permalink}"
    except Exception as e:
        print("Erreur lors de la récupération du dernier post de l'utilisateur")
        print("Message d'erreur :", str(e))
        return None


def get_user_comments(reddit, redditor, count=10):
    """
    Récupérer les 10 commentaires les plus pertinents de l'utilisateur spécifié sur Reddit.
    Retourne une liste de commentaires avec le nom d'utilisateur et les informations du compte associé.
    """
    comments = []

    try:
        user_submissions = redditor.submissions.new(limit=1)
        for submission in user_submissions:
            submission.comments.replace_more(limit=None)
            submission_comments = submission.comments.list()
            sorted_comments = sorted(submission_comments, key=lambda x: x.score, reverse=True)
            for comment in sorted_comments:
                user_data = get_user_data(reddit, comment.author.name)
                comments.append({
                    'username': comment.author.name,
                    'user_data': user_data,
                    'comment': comment.body
                })
    except Exception as e:
        print("Erreur lors de la récupération des commentaires de l'utilisateur")
        print("Message d'erreur :", str(e))

    return comments


def get_posts_from_hashtags(reddit, hashtags, count=10):
    """
    Récupérer les posts contenant les hashtags spécifiés sur Reddit en utilisant l'API PRAW.
    """
    user_data = {}  # Dictionnaire pour stocker les données des utilisateurs
    results = []

    for hashtag in hashtags:
        try:
            posts = reddit.subreddit("all").search(f"#{hashtag}", sort="new", limit=count)
            results.append(f"Requête réussie pour le hashtag #{hashtag}")
            results.append("")

            for post in posts:
                post_author = post.author.name
                # Récupérer les données de l'utilisateur et les stocker dans le dictionnaire
                user_data[post_author] = get_user_data(reddit, post_author)

                # Afficher le post avec les informations associées à l'utilisateur et le lien Reddit
                results.append(f"Post de l'utilisateur {post_author}:")
                results.append(f"Informations de l'utilisateur : {user_data[post_author]}")
                results.append(f"Lien Reddit du post : {post.url}")
                results.append("")

                # Vérifier si le post a des commentaires
                if post.num_comments > 0:
                    # Récupérer les commentaires pertinents de l'utilisateur et les afficher
                    comments = get_user_comments(reddit, post.author)
                    results.append("Commentaires :")
                    if len(comments) > 0:
                        for comment in comments[:count]:
                            results.append(f"\tUtilisateur : {comment['username']}")
                            results.append(f"\tInformations de l'utilisateur : {comment['user_data']}")
                            results.append(f"\tCommentaire : {comment['comment']}")
                            results.append("")
                    else:
                        results.append("\tAucun commentaire pertinent trouvé.")
                    results.append("")
                else:
                    results.append(f"Aucun commentaire sur le post de l'utilisateur {post_author}.")
                    results.append("")

        except Exception as e:
            print("Erreur lors de la récupération des posts pour le hashtag", hashtag)
            print("Message d'erreur :", str(e))

    # Trier les utilisateurs par popularité (karma total) et les afficher avec les autres informations
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['karma_total'], reverse=True)
    results.append("\nRésultats triés par popularité :")
    for user, data in sorted_users:
        results.append("------")
        results.append(f"Utilisateur : {user}")
        results.append("Informations de l'utilisateur :")
        results.append(f"Karma total : {data['karma_total']}")
        # Afficher d'autres informations de l'utilisateur si nécessaire
        results.append(f"Lien vers le post sur Reddit : {data['post_link']}")
        results.append("")

    return results


def main():
    # Hashtags à rechercher
    hashtags = ["Wagner", "Poutine"]

    load_dotenv()  # Charger les variables d'environnement depuis le fichier .env

    reddit = praw.Reddit(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT")
    )

    # Récupérer les posts contenant les hashtags et les afficher avec les informations utilisateur triées par popularité
    results = get_posts_from_hashtags(reddit, hashtags, count=10)

    app = QApplication(sys.argv)
    window = RedditResultsWindow()
    window.display_results(results)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
