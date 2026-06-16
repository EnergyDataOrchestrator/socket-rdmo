from rdmo.questions.models import Catalog, Section, QuestionSet, Question
from rdmo.domain.models import Attribute
from rdmo.options.models import Option, OptionSet

models = [Option, OptionSet, Question, QuestionSet, Section, Catalog, Attribute]

for model in models:
    items = model.objects.filter(uri__contains='kit.edu')
    for item in items:
        print(item.uri)
    count = items.count()
    if count > 0:
        items.delete()
        print(f"Deleted {count} instances from {model.__name__}")