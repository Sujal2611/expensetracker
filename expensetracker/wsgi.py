"""
WSGI config for expensetracker project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import nltk
import os

# Define a fixed path for NLTK data
nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
nltk.data.path.append(nltk_data_path)

# Ensure required NLTK packages are downloaded
nltk.download('punkt', download_dir=nltk_data_path)
nltk.download('stopwords', download_dir=nltk_data_path)
nltk.download('wordnet', download_dir=nltk_data_path)
nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_path)


from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expensetracker.settings')

application = get_wsgi_application()
