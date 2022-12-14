from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Todo(db.Model): #child model
  __tablename__ = 'todos'
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(), nullable=False)
  completed = db.Column(db.Boolean, nullable=False, default=False)
  #specify the foreign key on the child model
  list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)
  #list id references the id on the foreign table(parent)
  #db.Foreign key takes the table name of the parent dot the column name of the primary key

  def __repr__(self):
    return f'<Todo {self.id} {self.description}, list {self.list_id}>'

class TodoList(db.Model): #parent model
  __tablename__ = 'todolists'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  #specify the relationship on the parent model
  todos = db.relationship('Todo', backref='list', lazy=True)
  #name of the children is todos
  #Todo is a string referencing the name of a class,
  #backref equals to a custom name referencing the name of the parent.

  def __repr__(self):
    return f'<TodoList {self.id} {self.name}>'

#CREATE todo
@app.route('/todos/create', methods=['POST'])
def create_todo():
  error = False
  body = {}
  try:
    description = request.get_json()['description']
    list_id = request.get_json()['list_id']
    todo = Todo(description=description, list_id=list_id,completed=False)
    db.session.add(todo)
    db.session.commit()
    body['id'] = todo.id
    body['completed'] = todo.completed
    body['description'] = todo.description
    body['list_id'] = todo.list_id
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      abort (400)
    else:
      return jsonify(body)

#SET COMPLETED todo
@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
  try:
    completed = request.get_json()['completed']
    print('completed', completed)
    todo = Todo.query.get(todo_id)
    todo.completed = completed
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))

#DELETE todo
@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
  try:
    Todo.query.filter_by(id=todo_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({ 'success': True })


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
  return render_template('index.html',
  lists=TodoList.query.all(),
  active_list=TodoList.query.get(list_id),
  todos=Todo.query.filter_by(list_id=list_id).order_by('id').all()
)

@app.route('/')
def index():
  return redirect(url_for('get_list_todos', list_id=1))


if __name__ == '__main__':
  app.debug = True
  app.run(host="0.0.0.0")
