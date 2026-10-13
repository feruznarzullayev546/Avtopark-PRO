def branch_kwargs(request):
    bid = request.session.get('active_branch_id')
    if bid:
        return {'branch_id': bid}
    return {}

def relation_branch_kwargs(request, relation='branch'):
    bid = request.session.get('active_branch_id')
    return {f'{relation}__id': bid} if bid else {}
