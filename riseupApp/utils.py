import json

class UIMsg:
    title = ""
    message = ""
    
    def __init__(self, title, message):
        self.title = title
        self.message = message
        
    def to_dict(self):
        return {
            "title": self.title,
            "message": self.message
        }
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict()) 