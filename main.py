from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///to_do_lists.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)

    stages = relationship("Stage", back_populates="parent_project")


class Stage(db.Model):
    __tablename__ = "stages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=False, nullable=False)

    tasks = relationship("Task", back_populates="parent_stage")
    parent_project = relationship("Project", back_populates="stages")
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=False, nullable=False)

    stage_id = db.Column(db.Integer, db.ForeignKey("stages.id"))
    parent_stage = relationship("Stage", back_populates="tasks")


db.create_all()


class ProjectForm(FlaskForm):
    name = StringField("Project Name", validators=[DataRequired()])
    submit = SubmitField("Create")


class StageForm(FlaskForm):
    name = StringField("Stage Name", validators=[DataRequired()])
    submit = SubmitField("Create")


class TaskForm(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired()])
    submit = SubmitField("Create")


@app.route("/")
def home():
    projects = Project.query.all()
    return render_template("index.html", projects=projects)


@app.route("/project/<int:project_id>")
def show_project(project_id):
    selected_project = Project.query.get(project_id)
    stages = selected_project.stages
    try:
        last_stage = stages[-1]
    except IndexError:
        last_stage = None
    stage_id = None
    return render_template("show_project.html", stages=stages, stage_id=stage_id,
                           last_stage=last_stage, project_id=project_id, project=selected_project)


@app.route("/create_project", methods=["GET", "POST"])
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
        )
        db.session.add(new_project)
        db.session.commit()
        project_id = Project.query.all()[-1].id
        return redirect(url_for("show_project", project_id=project_id))

    return render_template("create_project.html", form=form)


@app.route("/create_stage/<int:project_id>", methods=["GET", "POST"])
def create_stage(project_id):
    form = StageForm()
    parent_project = Project.query.get(project_id)
    if form.validate_on_submit():
        new_stage = Stage(
            name=form.name.data,
            parent_project=parent_project,
        )
        db.session.add(new_stage)
        db.session.commit()
        return redirect(url_for("show_project", project_id=project_id))

    return render_template("create_stage.html", form=form)


@app.route("/create_task/<int:project_id>", methods=["GET", "POST"])
def create_task(project_id):
    form = TaskForm()
    current_project = Project.query.get(project_id)
    parent_stage = current_project.stages[0]
    if form.validate_on_submit():
        new_task = Task(
            name=form.name.data,
            parent_stage=parent_stage,
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("show_project", project_id=project_id))

    return render_template("create_task.html", form=form)


@app.route("/delete_task/<int:project_id>/<int:task_id>")
def delete_task(project_id, task_id):
    selected_task = Task.query.get(task_id)
    db.session.delete(selected_task)
    db.session.commit()

    return redirect(url_for("show_project", project_id=project_id))


@app.route("/complete_task/<int:project_id>/<int:stage_id>/<int:task_id>")
def complete_task(task_id, stage_id, project_id):
    selected_task = Task.query.get(task_id)
    selected_stage = Stage.query.get(stage_id)
    stages = Stage.query.all()
    for index, stage in enumerate(stages):
        try:
            if stage == selected_stage:
                next_stage = stages[index + 1]
                new_task = Task(
                    name=selected_task.name,
                    parent_stage=next_stage
                )
                db.session.add(new_task)
                db.session.delete(selected_task)
                db.session.commit()
        except IndexError:
            pass

    return redirect(url_for("show_project", project_id=project_id))


if __name__ == '__main__':
    app.run(debug=True)
