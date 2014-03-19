from app import db, models
def borrarState():
    state = models.StateSurvey.query.all()
    for s in state:
        db.session.delete(s)
    db.session.commit()

def borrarRespuestas():
    for ans in models.Answer.query.all():
        db.session.delete(ans)
    db.session.commit()
    borrarState()

def verState():
    state = models.StateSurvey.query.all()
    for s in state:
        print "id", s.id, "user", s.user_id, "survey:", s.survey_id, "status", s.status
    

def verAnswers():
    for ans in models.Answer.query.all():
        print ans.id, "user", ans.user.nickname, ans.question_id, ans.question.text
        if ans.question.type=='yn':
            print ans.answerYN
        if ans.question.type =='numerical':
            print ans.answerNumeric
        if ans.question.type== 'text':
            print ans.answerText
        if ans.question.type== 'choice':
            print ans.answerNumeric
        if ans.question.type== 'partTwo':
            print ans.answerNumeric
        if ans.question.type== 'decisionOne':
            print ans.answerNumeric
        if ans.question.type =='decisionTwo':
            print ans.answerNumeric
        if ans.question.type =='decisionThree':
            print ans.answerNumeric
        if ans.question.type =='decisionFour':
            print ans.answerNumeric
        if ans.question.type =='decisionFive':
            print ans.answerYN
        if ans.question.type =='decisionSix':
            print ans.answerNumeric
        print "global:",  ans.globalTime
        print "diferencial:", ans.differentialTime 
        print '================================='

def verPreguntas():
    for q in models.Question.query.all():
        print q.id, q.text, q.type
        if q.type =='partTwo':
            for index,i in enumerate(q.choicesPartTwo):
                print "  ", index, i


def generateUserFake(count=100):
    from sqlalchemy.exc import IntegrityError
    from random import seed
    import forgery_py

    seed()
    for i in range(count):
        u = models.User(email=forgery_py.internet.email_address(),
                 nickname=forgery_py.internet.user_name(True))
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def verUsuarios():
    for u in models.User.query.all():
        print u.id, u.email, u.nickname

def generateUserFake1(count=100):
    from sqlalchemy.exc import IntegrityError

    for i in range(count):
        u = models.User(email="user"+str(i)+"gmail.com",
                 nickname="user"+str(i))
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def verMatching():
    for m in models.Match.query.all():
        print "userA: " , m.userA, "userB: ", m.userB
        print "win: ", m.win
        print "moneyA: ", m.moneyA, "moneyB", m.moneyB
        print "type: ", m.type
        print "__________________"

def borrarMatching():
    ms = models.Match.query.all()
    for m in ms:
        db.session.delete(m)
    db.session.commit()


def generateAnswerFakePart3(id_survey, number = 6):
    #doy por echo que existen ya lso 100 usuarios de generarUserFake1
    #relleno aleatoriamente uan encuesta con preguntas del tipo decisiones
    import random
    random.seed()
    l=[0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10]
    l2=[0,2,4,6,8,10,12,14,16,18,20]
    question1 = models.QuestionDecisionOne.query.filter(models.QuestionDecisionOne.section_id==24).first()
    question2 = models.QuestionDecisionTwo.query.filter(models.QuestionDecisionTwo.section_id==25).first()
    question3 = models.QuestionDecisionThree.query.filter(models.QuestionDecisionThree.section_id==26).first()
    question4 = models.QuestionDecisionFour.query.filter(models.QuestionDecisionFour.section_id==27).first()
    questions5 = models.QuestionDecisionFive.query.filter(models.QuestionDecisionFive.section_id==28)
    question6 = models.QuestionDecisionSix.query.filter(models.QuestionDecisionSix.section_id==29).first()

    for i in range(2,number+2):
        user = models.User.query.filter(models.User.nickname=="user"+str(i)).first()
        ss, error =models.StateSurvey.getStateSurvey(id_survey,user,"192.168.0.0")
        ss.status= ss.status | models.StateSurvey.FINISH | models.StateSurvey.FINISH_OK
        db.session.add(ss)
        answer1=models.Answer(answerNumeric=random.choice(l),user=user,question=question1)
        db.session.add(answer1)
        answer2=models.Answer(answerNumeric=random.choice(l),user=user,question=question2)
        db.session.add(answer2)
        answer3=models.Answer(answerNumeric=random.choice(l),user=user,question=question3)
        db.session.add(answer3)
        answer4=models.Answer(answerNumeric=random.choice(l2),user=user,question=question4)
        db.session.add(answer4)  
        aceptas=random.randrange(0,2)==1
        for q in questions5:
            if not aceptas:
                answer5=models.Answer(answerYN=False,user=user,question=q)
                aceptas=random.randrange(0,2)==1
            else:
                answer5=models.Answer(answerYN=True,user=user,question=q)
            db.session.add(answer5)
        answer6=models.Answer(answerNumeric=random.choice(l2),user=user,question=question6)
        db.session.add(answer6)  


    db.session.commit()

def generate_answers_fake(id_survey, number=6):
    '''responding to the survey(id_survey) randomly 
    '''
    import random
    import forgery_py
    from app.models import Survey, Consent, Section, Answer, User, StateSurvey
    from app.models import Question, QuestionChoice, QuestionNumerical, QuestionText
    from app.models import QuestionYN ,QuestionLikertScale, QuestionPartTwo, QuestionDecisionOne,\
      QuestionDecisionTwo, QuestionDecisionThree, QuestionDecisionFour, \
      QuestionDecisionFive, QuestionDecisionSix    


    def answer_question(user,q, time):
        l=[0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10]
        l2=[0,2,4,6,8,10,12,14,16,18,20]
        if isinstance (q, QuestionYN):
            answer = Answer (answerYN =random.randrange(0,2)==1, user= user, question = q)
        elif isinstance (q, QuestionNumerical):
            answer = Answer (answerNumeric =random.randrange(0,100), user= user, question = q)
        elif isinstance (q, QuestionText):
            if q.isExpectedAnswer():
                if random.choice([0,1,1])==1:
                # 66% of know the answer
                    answer = Answer (answerText =q.expectedAnswer.lower(), user= user, question = q)
                    answer.numberAttempt= random.range(1, q.maxNumberAttempt+1)
                else:
                    answer = Answer (answerText =forgery_py.forgery.lorem_ipsum.word(), user= user, question = q)
                    answer.numberAttempt= q.maxNumberAttempt+1
            elif q.isNumber:
                answer = Answer (answerNumeric =random.randrange(0,100), user= user, question = q)
            else:
                answer = Answer (answerText =forgery_py.forgery.lorem_ipsum.word(), user= user, question = q)
        elif isinstance (q,QuestionChoice):
            answer = Answer (answerNumeric =random.randrange(0,len(q.choices)), user= user, question = q)
        elif isinstance (q,QuestionLikertScale):
            answer = Answer (answerNumeric =random.randrange(q.minLikert,q.maxLikert+1), user= user, question = q)
        elif isinstance (q, QuestionPartTwo):
            answer = Answer (answerNumeric =random.randrange(0,2), user= user, question = q)
        elif isinstance (q, QuestionDecisionOne):
            answer=models.Answer(answerNumeric=random.choice(l),user=user,question=q)
        elif isinstance (q, QuestionDecisionTwo):
            answer=models.Answer(answerNumeric=random.choice(l),user=user,question=q)
        elif isinstance (q, QuestionDecisionThree):
            answer=models.Answer(answerNumeric=random.choice(l),user=user,question=q)
        elif isinstance (q, QuestionDecisionFour):
            answer=models.Answer(answerNumeric=random.choice(l2),user=user,question=q)
        elif isinstance (q, QuestionDecisionFive):
            answer = Answer (answerYN =random.randrange(0,2)==1, user= user, question = q)
        elif isinstance (q, QuestionDecisionSix):
            answer=models.Answer(answerNumeric=random.choice(l2),user=user,question=q)
        else:
            print "tipo de pregunta invalido"
            quit()
        t = random.randrange(900, 6500)
        time = time + t
        answer.globalTime = time
        answer.differentialTime = t
        db.session.add(answer)
        return time

    borrarRespuestas()
    random.seed()
    for i in range(2,number+2):
        user = User.query.get(i);
        ss, error = StateSurvey.getStateSurvey(id_survey,user,forgery_py.forgery.internet.ip_v4())
        if error != StateSurvey.NO_ERROR:
            print "error en fechas o en algo"
            quit()
        ss.accept_consent()
        while not ss.is_finished():
            section = ss.nextSection()
            questions = section.questions
            time = 0
            for question in questions:
                time = answer_question(user,question, time)
            db.session.commit()
            time = time + random.randrange(100, 500)
            ss.finishedSection(time)
