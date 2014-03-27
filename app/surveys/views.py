# -*- coding: utf-8 -*-
from app import app, db
from flask import Blueprint, request, url_for, flash, redirect, abort, session, g
from flask import render_template
from flask.ext.login import login_user, logout_user, current_user, login_required
from forms import LoginForm, AnswerChoiceForm, AnswerNumericalForm, AnswerTextForm, AnswerYNForm
from app.models import Survey, Consent, Section
from app.models import Question, QuestionChoice, QuestionNumerical, QuestionText
from app.models import QuestionYN ,QuestionLikertScale
from app.models import StateSurvey
from app.models import Answer
from flask.ext.wtf import Form
from sqlalchemy.sql import func
from wtforms import TextField, BooleanField, RadioField, IntegerField, HiddenField
from wtforms.validators import Required, Regexp, Optional
from wtforms import ValidationError
import datetime
from . import blueprint
from app.decorators import valid_survey, there_is_stateSurvey
from ..main.errors import ErrorEndDateOut, ErrorExceeded, ErrorTimedOut


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    '''
    shows all available surveys
    '''
    stmt1 = db.session.query(StateSurvey.survey_id, StateSurvey.status).\
        filter(StateSurvey.user==current_user).subquery()
    
    stmt2 = db.session.query(StateSurvey.survey_id, func.count('*').label('r_count')).\
        filter(StateSurvey.status.op('&')(StateSurvey.FINISH_OK)).\
        group_by(StateSurvey.survey_id).subquery()

    now = datetime.datetime.utcnow()
    #outerjoint Survey and StateSurvey(with the currentUser) and number of user
    # that have made the survey
    surveys = db.session.query(Survey, stmt1.c.status, stmt2.c.r_count).\
        outerjoin(stmt1,Survey.id==stmt1.c.survey_id).\
        outerjoin(stmt2,Survey.id==stmt2.c.survey_id).\
        filter(Survey.startDate<now,Survey.endDate>now).\
        order_by(Survey.startDate)
    return render_template('/surveys/index.html',
        title = 'Index',
        # surveys= [s.Survey for s in surveys],
        surveys = surveys) 

def get_stateSurvey_or_error(id_survey,user,ip = None):
    stateSurvey, status = StateSurvey.getStateSurvey(id_survey,user,ip)
    if status == StateSurvey.NO_ERROR:
        return stateSurvey
    else:
        if status == StateSurvey.ERROR_EXCEEDED:
            raise ErrorExceeded
        if status == StateSurvey.ERROR_TIMED_OUT:
            raise ErrorTimedOut
        if status == StateSurvey.ERROR_END_DATE_OUT:
            raise ErrorEndDateOut
        if status == StateSurvey.ERROR_NO_SURVEY:
            return abort(404)
        return abort(500)    



@login_required
@blueprint.route('/survey/<int:id_survey>', methods=['GET', 'POST'])
@valid_survey
def logicSurvey(id_survey):
    '''
    Function that decides which is the next step in the survey
    '''
    stateSurvey = get_stateSurvey_or_error(id_survey,g.user,request.remote_addr)

    if (stateSurvey.consented == False):
        return redirect(url_for('surveys.showConsent', id_survey = id_survey))
    section = stateSurvey.nextSection()
    if section is None:
        if stateSurvey.status & StateSurvey.FINISH_OK:
            return render_template('/surveys/finish.html', 
                title = 'Finish')
        if stateSurvey.status & StateSurvey.TIMED_OUT:
            return render_template('/survey/error_time_date.html',
                title ='time out')
        if stateSurvey.status & StateSurvey.END_DATE_OUT:
            return render_template('/survey/error_time_date.html',
                title ='End date out')
        return abort(500) 
    return redirect (url_for('surveys.showQuestions',id_survey=id_survey,id_section=section.id))

@login_required
@blueprint.route('/survey/<int:id_survey>/consent', methods=['GET', 'POST'])
@blueprint.route('/survey/<int:id_survey>/consent/<int:n_consent>', methods=['GET', 'POST'])
@valid_survey
@there_is_stateSurvey
def showConsent(id_survey,n_consent = 0):
    '''
    Show consent, n_consent is the "position of consent", no id!!
    '''
    
    survey = Survey.query.get(id_survey)
    consents = survey.consents

    if n_consent>consents.count():
        abort (404)

    if consents.count()==0:
        stateSurvey = get_stateSurvey_or_error(id_survey,g.user)
        stateSurvey.accept_consent()
        return redirect(url_for('surveys.logicSurvey',id_survey = id_survey))
    
    if request.method == 'POST' and consents.count()<=n_consent+1:
        stateSurvey = get_stateSurvey_or_error(id_survey,g.user)
        stateSurvey.accept_consent()
        return redirect(url_for('surveys.logicSurvey',id_survey = id_survey))

    if request.method == 'POST' and consents.count()>n_consent+1:
        return redirect(url_for('surveys.showConsent', id_survey = id_survey, n_consent = n_consent+1))


    return render_template('/surveys/consent.html',
        title = survey.title,
        survey = survey,
        consent = survey.consents[n_consent])


def generate_form(questions):
    '''dynamically generates the forms for surveys
    '''
    # def check_answer_expected(id_question):
    #     print "VAMOS ATOMOS", id_question
    #     def _check_answer_expected(self, field):
    #         question = Question.query.get(id_question)
    #         expected_answer = question.expectedAnswer
    #         print "VAMOS ATOMOSsss"
    #         if field.data!=expected_answer:
    #             raise ValidationError("respuesta erronea")
    def check_answer_expected(self,field):
        '''check if the answer is the expected
        '''
        question = Question.query.get(field.name[1:])
        answer = Answer.query.filter(Answer.user_id==g.user.id,
                Answer.question_id==question.id).first()
        if answer is None:
            answer = Answer (answerText = field.data, user= g.user, question = question)
            answer.globalTime = form["globalTimec"+str(question.id)].data
            answer.differentialTime = form["differentialTimec"+str(question.id)].data
        else:
            answer.answerText = field.data
        db.session.add(answer)
        db.session.commit()
        if not answer.answerAttempt():
            if answer.isMoreAttempt():
                raise ValidationError("Wrong answer")
            else:
                flash("wrong answer, you can continue")

    class AnswerForm(Form):
        time = HiddenField('time',default=0)

    for question in questions:

        setattr(AnswerForm,"globalTimec"+str(question.id),HiddenField('globalTimec'+str(question.id),default=0))
        setattr(AnswerForm,"differentialTimec"+str(question.id),HiddenField('differentialTimec'+str(question.id),default=0))

        #added "c" to that the key is valid
        #First element must be a string, otherwise fail to valid choice

        if isinstance (question,QuestionYN):
            if question.required:
                setattr(AnswerForm,"c"+str(question.id),RadioField('Answer', 
                    choices = [('Yes','Yes'),('No','No')],validators = [Required()]))
            else:
                setattr(AnswerForm,"c"+str(question.id),RadioField('Answer', 
                    choices = [('Yes','Yes'),('No','No')],validators = [Optional()]))
        if isinstance (question,QuestionNumerical):
            if question.required:
                setattr(AnswerForm,"c"+str(question.id),IntegerField('Answer'))
            else:
                setattr(AnswerForm,"c"+str(question.id),IntegerField('Answer'),validators = [Optional()])
        if isinstance (question,QuestionText):
            if question.required:
                if question.regularExpression !="":
                    setattr(AnswerForm,"c"+str(question.id),TextField('Answer',
                        validators=[Required(), Regexp(question.regularExpression,0,question.errorMessage)]))
                elif question.isExpectedAnswer():
                    setattr(AnswerForm,"c"+str(question.id),TextField('Answer',validators = [Required(),
                        check_answer_expected]))
                elif question.isNumber:
                    setattr(AnswerForm,"c"+str(question.id),IntegerField('Answer'))
                else:
                    setattr(AnswerForm,"c"+str(question.id),TextField('Answer',validators = [Required()]))
            else:
                if question.regularExpression !="":
                    setattr(AnswerForm,"c"+str(question.id),TextField('Answer',
                        validators=[Optional(), Regexp(question.regularExpression,0,question.errorMessage)]))
                elif question.isNumber:
                    setattr(AnswerForm,"c"+str(question.id),IntegerField('Answer',validators = [Optional()]))
                else:
                    setattr(AnswerForm,"c"+str(question.id),TextField('Answer',validators = [Optional()]))
        if isinstance (question,QuestionChoice):
            list = [(str(index),choice) for index, choice in enumerate(question.choices)]
            if question.required:
                setattr(AnswerForm,"c"+str(question.id),RadioField('Answer', 
                    choices = list,validators = [Required()]))
            else:
                setattr(AnswerForm,"c"+str(question.id),RadioField('Answer', 
                    choices = list,validators = [Optional()]))

        if isinstance (question, QuestionLikertScale):
            list = [(str(index),index) for index in range(question.minLikert,question.maxLikert+1)]
            if question.required:
                setattr(AnswerForm,"c"+str(question.id),RadioField('Answer', 
                    choices = list,validators = [Required()]))
            else:
                setattr(AnswerForm,"c"+str(question.id),RadioField('Answer', 
                    choices = list,validators = [Optional()]))

    form = AnswerForm()
    return form


@login_required
@blueprint.route('/survey/<int:id_survey>/section/<int:id_section>', methods=['GET', 'POST'])
@valid_survey
@there_is_stateSurvey
def showQuestions(id_survey, id_section):
    '''
    Show all question of a section
    '''
    stateSurvey = get_stateSurvey_or_error(id_survey,g.user,request.remote_addr)
    section = stateSurvey.nextSection()
    if section is None or section.id !=id_section:
        flash ("access denied")
        return abort (403)
        
    survey = Survey.query.get(id_survey)
    section = Section.query.get(id_section)
    questions = section.questions
   
    form = generate_form(questions)
    if form.validate_on_submit():
        for question in questions:
            if isinstance (question,QuestionYN):
                answer = Answer (answerYN = (form["c"+str(question.id)].data=='Yes'), user= g.user, question = question)
            if isinstance (question,QuestionNumerical):
                answer = Answer (answerNumeric = form["c"+str(question.id)].data, user= g.user, question = question)
            if isinstance (question,QuestionText):
                if question.isNumber:
                    answer = Answer (answerNumeric = form["c"+str(question.id)].data, user= g.user, question = question)
                else:
                    answer = Answer (answerText = form["c"+str(question.id)].data, user= g.user, question = question)
            if isinstance (question,QuestionChoice):
                answer = Answer (answerNumeric = form["c"+str(question.id)].data, user= g.user, question = question)
            if isinstance (question, QuestionLikertScale):
                answer = Answer (answerNumeric = form["c"+str(question.id)].data, user= g.user, question = question)

            answer.globalTime = form["globalTimec"+str(question.id)].data
            answer.differentialTime = form["differentialTimec"+str(question.id)].data
            db.session.add(answer)
            db.session.commit()

        stateSurvey.finishedSection(form.time.data)
        return redirect(url_for('surveys.logicSurvey',id_survey = id_survey))

    return render_template('/surveys/showQuestions.html',
            title = survey.title,
            survey = survey,
            section = section,
            # form = form,
            form = form,
            questions = questions,
            percent = stateSurvey.percentSurvey()
            )
