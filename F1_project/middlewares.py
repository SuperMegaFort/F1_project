from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request

class HandleOffsiteMiddleware(object):
    def process_request(self, request, spider):
        print(f"Middleware: Processing request: {request.url}")  # Debug print
        if 'real_url' in request.meta:
            real_url = request.meta['real_url']
            print(f"Middleware: Found real_url: {real_url}")  # Debug print

            # Use request.replace() and *explicitly* keep the callback
            new_request = request.replace(url=real_url)
            new_request.callback = request.callback # VERY IMPORTANT

            print("Middleware: Raising IgnoreRequest")  # Debug print
            raise IgnoreRequest # We still raise the exception
        print("Middleware: Returning None") # Debug print
        return None