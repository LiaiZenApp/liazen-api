# Member service logic

def get_member(userId):
    return {"member": userId}

def get_member_by_email(email):
    return {"email": email}

def create_member(member):
    return {"created": True}

def delete_member(id):
    return {"deleted": id}

def get_relationships():
    return ["friend", "family"]

def invite_member(data):
    return {"invited": True}
