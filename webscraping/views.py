import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from dashboards.forms import URLForm
from dashboards.models import Dataset, Profile, Activity
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import requests
from bs4 import BeautifulSoup
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class WebScrapingView(View):
    USAGE_LIMIT = 5  # Define your free usage limit here

    @method_decorator(login_required, name='dispatch')
    def get(self, request):
        """
        Displays the form for web scraping.
        """
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= self.USAGE_LIMIT:
            return redirect('prompt_payment')

        form = URLForm()
        return render(request, 'webscraping.html', {'form': form})

    @method_decorator(login_required, name='dispatch')
    def post(self, request):
        """
        Handles the form submission to scrape data from a URL.
        """
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= self.USAGE_LIMIT:
            return redirect('prompt_payment')

        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract the title
                title = soup.title.string if soup.title else 'No title found'

                # Extract text from all <p> tags
                paragraphs = soup.find_all('p')
                content = "\n".join([p.get_text() for p in paragraphs])

                # Store the title and content in the session
                request.session['scraped_data'] = {
                    'title': title,
                    'content': content,
                    'url': url
                }

                try:
                    with transaction.atomic():
                        # Update service usage count for the user if they don't have an active subscription
                        if not profile.has_active_subscription():
                            profile.service_usage_count += 1
                        profile.save()

                        # Log activity
                        activity = Activity(
                            user=request.user,
                            activity_type='Web Scraping',
                            dataset=None,
                            uploaded_file=None
                        )
                        activity.save()

                    return render(request, 'webscraping_result.html', {'title': title, 'content': content, 'url': url})
                except Exception as e:
                    logger.error(f"Error updating service usage or logging activity: {e}")
                    form.add_error(None, 'An error occurred while updating service usage or logging activity.')
            else:
                form.add_error('url', 'Failed to retrieve the URL')

        return render(request, 'webscraping.html', {'form': form})

@login_required
def download_excel(request):
    """
    Handles the download of scraped data as an Excel file.
    """
    scraped_data = request.session.get('scraped_data', None)
    if not scraped_data:
        return redirect('webscraping')  # Redirect to the scraping page if there's no data

    # Create a DataFrame with the scraped data
    df = pd.DataFrame([{
        'Title': scraped_data['title'],
        'Content': scraped_data['content']
    }])

    # Create a HttpResponse object with the correct content_type for Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="scraped_data.xlsx"'
    
    # Use pandas to write the DataFrame to an Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Scraped Data')

    return response
