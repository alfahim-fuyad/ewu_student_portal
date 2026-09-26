"""
Chatbot views — single endpoint for posting questions + history fetcher.

Both require login so we can attach messages to the user.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from chatbot.services import respond, get_recent_history


@login_required
@require_http_methods(['POST'])
def chat(request):
    """POST {question} → JSON {reply, intent, allowed}."""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    question = (payload.get('question') or '').strip()
    if not question:
        return JsonResponse({'error': 'Question cannot be empty'}, status=400)

    try:
        result = respond(request.user, question)
    except Exception as e:
        # Always return something useful — never crash the chat window
        return JsonResponse({
            'error': 'Internal server error',
            'detail': str(e),
            'reply': '🤖 Sorry, something went wrong on my end. Please try again.',
            'intent': 'error',
            'allowed': False,
        }, status=500)

    return JsonResponse(result)


@login_required
def history(request):
    """GET → JSON list of recent chat exchanges."""
    limit = request.GET.get('limit', 10)
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    rows = get_recent_history(request.user, limit=limit)
    return JsonResponse({'history': rows})


@login_required
def clear(request):
    """POST → delete the user's chat history."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    from chatbot.models import ChatHistory
    ChatHistory.objects.filter(user=request.user).delete()
    return JsonResponse({'cleared': True})
