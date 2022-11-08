from flask import Flask, request, abort, jsonify
# from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"/api/*": {"origins": "*"}})
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):

    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods','GET,PUT,POST,DELETE,PATCH,OPTIONS')

    return response
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():

    categories = Category.query.order_by(Category.id).all()
    if categories is None:
        abort(404)
    print(categories)
    categories_list = []
    for category in categories:
        categories_list.append(
          category.type
        )

    return jsonify(
      {
        'success': True,
        'categories': categories_list
      }
    )

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  def paginate_questions(request, selection):

    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    questions_per_page = questions[start:end]

    return questions_per_page
  
  @app.route('/questions', methods=['GET'])
  def get_all_questions():

    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request=request, selection=questions)

    if len(current_questions) == 0:
      abort(404)

    categories = Category.query.order_by(Category.id).all()
    if categories is None:
      abort(404)

    categories_list = []
    for category in categories:
      categories_list.append(
        category.type
      )

    return jsonify(
      {
        'success': True,
        'questions': current_questions,
        'number_of_total_questions': len(questions),
        'current_category': categories_list,
        'categories': categories_list
      }
    )
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_questoin(question_id):

    print(question_id)
    question_to_delete = Question.query.filter(
      Question.id == question_id).one_or_none()
    if question_to_delete is None:
      abort(422)

    question_to_delete.delete()

    return jsonify(
      {
        'success': True,
        'deleted': question_id
      }
    )
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():

    data = request.get_json()

    try:
      new_question = Question(
        question=data['question'],
        answer=data['answer'],
        category=data['category'],
        difficulty=data['difficulty']
      )
    except:
      abort(422)

    new_question.insert()

    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request=request, selection=questions)

    return jsonify(
      {
        'success': True,
        'created': new_question.id,
        'questions': current_questions,
        'total_questions': len(questions)
      }
    )
  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['post'])
  def search_for_question():

    data = request.get_json()

    search_term = data.get('searchTerm', None)

    questions_list = Question.query.filter(
      Question.question.ilike('%' + search_term + '%')).all()
    questions_found = [question.format() for question in questions_list]

    if len(questions_list) == 0:
      abort(404)

    all_questions_count = Question.query.count()
    categories = Category.query.order_by(Category.id).all()

    if len(categories) == 0:
      abort(404)

    categories_list = []
    for category in categories:
      categories_list.append(
            category.type
      )

    return jsonify(
      {
        'success': True,
        'questions': questions_found,
        'total_questions': all_questions_count,
        'current_category': categories_list
      }
    )
  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 
  
  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  def __questions_by_category(category_id):
        if category_id == 0:
            data = Question.query.all()
        else:
            data = (
                Question.query.filter(Question.category == category_id).all()
            )
        return [q.format() for q in data]

  @app.route('/categories/<int:category>/questions')
  def questions_by_category(category):

    questions = __questions_by_category(category)
    total_questions = len(questions)
    if total_questions > 0:

      return jsonify(
        {
          "success": True,
          "questions": questions,
          "total_questions": total_questions,
          "current_category": category,
        }
      )
    else:
      abort(404)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    try:
            body = request.get_json()
            print(body)
            quiz_category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)
            print(quiz_category)
            if quiz_category['id'] == 0 :
                selection = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
                print(selection)
            else:
                selection = Question.query.filter(
                    Question.category == quiz_category['id'], Question.id.notin_(previous_questions)).all()

            formatted_questions = paginate_questions(request, selection)

            current_category = 0
            if len(formatted_questions) == 0:
                formatted_questions = ''
            else:
                formatted_questions = random.choice(formatted_questions)
                current_category = selection[0].category

            return jsonify({
                'success': True,
                'current_category': current_category,
                'question': formatted_questions,
                'total_questions': len(selection)
            })
    except:
      abort(400)
    
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(400)
  def bad_request(error):
      return (
        jsonify(
          {
            "success": False,
            "error": 400,
            "message": "bad request"
          }
        ), 400
      )

  @app.errorhandler(404)
  def not_found(error):
      return (
        jsonify(
          {
            "success": False, 
            "error": 404, 
            "message": "Not found"
          }
        ), 404,
      )

  @app.errorhandler(422)
  def unprocessable(error):
    return (
      jsonify(
        {
          "success": False, 
          "error": 422, 
          "message": "unprocessable"
        }
      ), 422,
      )

  return app

