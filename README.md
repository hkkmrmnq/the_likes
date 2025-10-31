The Likes, backend.
===========================================

The Likes is an app designed to find people with the same personal values. More detailed explanation below (also in Russian).

#### Tools used:
- Python 3.12
- Fastapi 0.116.1
- Fastapi-users (JWT) 14.0.1
- Sqlalchemy 2.0.41
- Alembic 1.16.4
- Celery[redis] 5.5.3
- PostgreSQL (postgis:18-3.6 Docker image)
- Docker compose
- Nginx
- Supervisor


Documentation file - 'documentation.json' - in backend folder.
To read - upload it to https://editor.swagger.io/


You can also use your own set of Values, Aspects and Attitudes. For this - edit backend/Basic data.xlsx and adjust Settings.PERSONAL_VALUE_MAX_ORDER.


#### To run project:


Clone
```bash
git clone git@github.com:hkkmrmnq/the_likes.git
```

Go to directory
```bash
cd the_likes
```

Create .env file
```
PG_USER=...  # user name for postgres
PG_PASSWORD=...  # password for postgres
PG_HOST=...   # postgres host
PG_PORT=...  # postgres port
PG_DB_NAME=...  # database name in postgres
JWT_SECRET=...   # create a secret key that will be used by JWT
RESET_PASSWORD_TOKEN_SECRET=...  # create a secret key that will be used by FastAPI Users
VERIFICATION_TOKEN_SECRET=  # create a secret key that will be used by FastAPI Users

# optional, google config (to use with your account - uncomment code in backend/src/tasks.py)
EMAIL_APP_EMAIL=...
EMAIL_APP_NAME=...
EMAIL_APP_PASSWORD=...
```

Run Docker network
```bash
make devup
```

Optional: add superuser
```shell
make devadmin
```

Access documentation: http://localhost/docs/

To put down docker network use
```bash
make devdown
```

If you want to keep db volumes between network buits - remove '-v' param in Makefile.


# Introduction for users

[Russian version](#введение-для-пользователей)


The Likes app allows you to find new connections based on your personal values.

I'm working from the following assumption.
1. Friendship begins and is maintained not by logic, but by emotion. We can be friends with someone who doesn't share our values — and not notice it amidst the positive emotions.
2. Over time (due to technological development, the spread of education, or some other reasons), people become more rational — relying less on emotions and more on logic, analysis, strategy, etc. This makes it more difficult for them to make new friends.
3. I don't think the process of rationalization can be stopped. If we want to preserve friendship, we must learn to begin new relationships not with emotion, but on rational grounds — personal values.

If successful, this project should become a push for the beginning of new, long—term, and strong relationships.
To do this, I propose defining your values — and based on this, the algorithm will select similar participants.

Since, as a rule, different people put different meanings into the same words, I suggest you not only choose values ​​that are close to yours, but also choose the meanings that you put into these terms.

Due to this approach, finding suitable users may take quite a while — and will certainly take time in the early stages, until a sufficient number of users have been recruited. I hope this won't discourage you.

If you want to know the reasons behind the choice of terms denoting values, here is the position from which I follow:

1. Reality exists independently of us and is knowable through experience. It can be understood as a set of all possible descriptive statements that denote either the very fact of our experience, or logically necessarily follow from the totality of facts.
2. Another type of statements are evaluative. We make evaluative statements about what we think reality should be like. Evaluative statements can take forms such as "X is good/bad, right/wrong" and "X should/should not be done".
3. Along with this, there is the concept of "moral values" — something like guidelines, relying on which we make evaluative statements.
4. Descriptive statements are logically connected with facts. Evaluative statements are also logically connected with moral values.
5. Further, I will use the term "values" in the following meaning. Values ​​are terms that:
• are highly abstract;
• work as moral guidelines (actions, words, thoughts, decisions, behavior of any person — will always to some extent be directed towards/from "love", "beauty", etc.);
• are ultimately unattainable, but can be pursued infinitely effectively (it is impossible to find all possible love in the universe, but we always can find more love);
• are neutral in themselves, until they are organized into a hierarchy (love in itself is neither good nor bad — we ourselves choose to what extent to strive for it / from it — and only this choice creates a hierarchy — places love above/below other moral values).
6. 
6.1. Each person has an internal hierarchy of values, which influences his emotions, thoughts, language, decisions and behavior, etc. And / or:
6.2. Every thought, word and action of each person influences the world in a certain way — as if shifting (even if only a little) in a certain direction. In some directions a person moves (and moves the world) more often, in some directions — less often.
6.3. Statements 6.1 and 6.2 are interchangeable in the context of reasoning about what (abstract moral) values ​​are: the set of directions and their "weights" is the same as an internal hierarchy of values.
7. Personal hierarchy of values ​​is not directly accessible to consciousness.
8. When attempting to define (or choose) a hierarchy of one's values, a second (conscious) hierarchy of values ​​is created in addition to the first (real) one. How similar the real and conscious value hierarchies will be for any given person is a question that is hardly possible to answer.
9. Since the real/unconscious is not completely isolated from the conscious, I propose that the unconscious value hierarchy can be changed through sustained conscious effort — through self-analysis and, most importantly, through discussion with people who share similar values.
Therefore, despite the obstacles, I propose this approach.


# Instructions for users

I offer you a set of terms denoting possible abstract values: Pleasure, Comfort, Happiness, Love, Beauty, Wealth, Status, Power, Violence, Truth, Freedom.

In the first step, you must select components — Aspects — for each value. If you agree that a statement should be included in the value definition, check the box next to it. For example, if you agree that Beauty is (partially or completely) an objective quality, include this aspect in the definition of beauty.

Choose your Aspects carefully. Each combination of Aspects is considered by the algorithm as an independent Value. That is, if you included the Aspect "objective quality" in Beauty, and someone else included all the same Aspects as you, but did not include "objective quality," we do not know how close or distant these two concepts are. Therefore, your Beauty and the Beauty of that other person are considered by the algorithm as Two completely different values ​​(despite the same name – Beauty).

In the second step, distribute the Values ​​among three groups: positive, negative, and neutral. Initially, all Values ​​are in the neutral group. If, for example, you want more Beauty in reality, move it to the positive group. If, conversely, you believe there should be less Beauty, move it to the negative group. If you want neither more nor less Beauty, leave it in the neutral group. Distribute all Values ​​according to this principle.

Positive and negative Values ​​should be arranged hierarchically, according to how you feel about them: in first place among the positive — the Value most dear to you, in second place is the next most dear, and so on. Negative Values: in last place is the most unpleasant and undesirable, in second to last is the almost most unpleasant/undesirable, and so on. Neutral values ​​do not need to be sorted — their order doesn't matter.

This task may require considerable deliberation. It's best to make a decision when you can identify the two most desired and two least desired values. Though the values ​​can be ordered any way you like — all decisions will be taken into account — preference will be given to the first two positive and last two negative values. (Here, I'm assuming that in most cases a person have at least 2 positive and two negative values, and those values are most decisive.)
You can change your value profile later, but frequent changes will reduce your chances of making friends.

In the third step, you'll choose a statement that characterizes your overall attitude toward values.


# Введение для пользователей

The Likes позволяет найти новых знакомых на основе персональных ценностей.

Я исхожу из следующего предположения.
1. Дружба начинается и поддерживается не логикой, а эмоциями. Мы можем дружить с человеком, который не разделяет наших ценностей — и не замечать этого на фоне положительных эмоций.
2. С течением времени (из-за технического развития, распространения образования, или ещё каких—то причин) люди становятся более рациональными — меньше полагаются на эмоции, и больше — на логику, анализ, статегию и т.п. Поэтому им становится труднее заводить новых друзей.
3. Не думаю, что процесс рационализации может быть остановлен. Если мы хотим сохранить дружбу, то должны учиться начинать новые отношения не с помощью эмоций, а на рациональных основаниях — персональных ценностях.

В случае успеха, этот проект должен стать толчком для начала новых длительных и крепких отношений.
Для этого предлагаю определить ваши ценности — и на основе этого алгоритм подберёт похожих участников.

Поскольку, как-правило, разные люди вкладывают разный смысл в одни и те же слова — я предлагаю вам не только выбрать ценности, близкие вашим, но и выбрать те смыслы, которые вы вкладываете в эти термины.

В связи с таким подходом, поиск подходящих пользователей может занять довольно продолжительное время — и наверняка займёт на раннем этапе — пока не наберётся достаточное количество пользователей. Надеюсь, это вас не отпугнёт.

Если вы хотите узнать, чем обусловлен выбор терминов, обозначающих ценности — вот позиция, из которой я исхожу:

1. Реальность существует независимо от нас и познаваема посредством опыта. Её можно понимать как совокупность всех возможных описательных утверждений, которые обозначают либо сам факт нашего опыта, либо логически необходимо следуют из всей совокупности фактов.
2. Ещё один тип утверждений — оценочные. Мы делаем оценочные утверждения о том, какой, по нашему мнению, должна быть реальность. Оценочные утверждения могут иметь такие формы, как «X — это хорошо/плохо, правильно/неправильно» и «следует / не следует сделать X».
3. Вместе с этим существует понятие "моральные ценности" — нечто, вроде ориентиров, опираясь на которые мы и делаем оценочные утверждения.
4. Описательные утверждения логически связаны с фактами. Оценочные утверждения — так же логически — связаны с моральными ценностями.
5. Далее я буду употреблять термин "ценности" в следующем значении. Ценности — это термины, которые:
• высоко-абстрактны;
• работают как моральные ориентиры (действия, слова, мысли, решения, поведение любого человека — всегда в какой—то степени будут направлены к/от "любви", "красоты" и т.п.);
• финально не достижимы, но их можно бесконечно эффективно преследовать (невозможно обрести всю возможную любовь во вселенной, но но всегда можно найти больше любви);
• нейтральны сами по себе, пока не организованы в иерархию (любовь сама по себе — ни хорошая, ни плохая — мы сами выбираем, в какой степени стремиться к ней / от неё — и только этот выбор создаёт иерархию — помещает любовь выше/ниже других моральных ценностей).
6. 
6.1. У каждого человека есть внутренняя иерархия ценностей, которая оказывает влияние на его эмоции, мысли, язык, решения и поведение и т.д. И / или:
6.2. Каждая мысль, слово и действие каждого человека оказывает влияние на мир вокруг, изменяя его определённым образом — смещая (даже если совсем немного) в определённом направлении. В каких—то направлениях человек двигается (и двигает мир) чаще, в каких—то — реже.
6.3. Утверждения 6.1 и 6.2 взаимозаменяемы в контексте рассуждения о том, что такое (абстрактные моральные) ценности: набор направлений и их "весов" — это то же самое, что внутренняя иерархия ценностей.
7. Персональная иерархия ценностей недоступна сознанию напрямую. Мы можем попытаться определить её интуитивно, но не существует способа проверить ценности человека.
8. При попытке определить (или выбрать) иерархию своих ценностей — помимо первой  (реальной) создаётся вторая (сознательная) иерархия ценностей. Насколько схожими будут реальная и сознательная иерархии ценностей у какого—то конкретного человека — это вопрос, на который вряд ли возможно ответить.
9. Поскольку реальное/бессознательное не в полной мере изолировано от сознательного, я предполагаю, что бессознательную иерархию ценностей можно изменить с помощью длительных сознательных усилий — через самоанализ и, что особенно важно, через обсуждение с людьми, имеющими схожие ценности.
Поэтому, несмотря на препятствия, я предлагаю этот подход.


# Инструкция для пользователей

Предлагаю вам набор терминов, означающих возможные абстрактные ценности: Удовольствие, Комфорт, Счастье, Любовь, Красота, Богатство, Статус, Власть, Насилие, Истина, Свобода.

На первом этапе для каждой ценности необходимо выбрать составляющие — Аспекты. Если вы согласны с тем, что утверждение должно быть включено в определение ценности, — поставьте галочку рядом с ним. Например, если вы согласны, что Красота — это (частично или полностью) объективное качество — включите этот аспект в опредение красоты.

Внимательно выбирайте Аспекты. Каждая комбинация Аспектов рассматривается алгоритмом как самостоятельная Ценность. То есть, если вы включили Аспект "объективное качество" в Красоту, а кто—то другой включил в Красоту все те же Аспекты, что и вы, но не включил "объективное качество" — мы не знаем, насколько близки или далеки эти два понятия. Поэтому, ваша Красота, и Красота того второго человека рассматриваются алгоритмом как две совершенно разные ценнсти (несмотря на одинаковое название — Красота).

На втором этапе распределите Цености между тремя группами: позитивные, негативные и нейтральные. Вначале все Ценности находятся в нейтральной группе. Если, например, вы хотите, чтобы в реальности было больше Красоты, — переместите её в группу позитивных. Если, наоборот, считаете, что Красоты должно быть меньше — переместите в группу негативных. Если же не хотите ни больше, ни меньше Красоты — оставьте её в нейтральной группе. По такому принципу распределите все Ценности.

Позитивные и негативные Ценности нужно располжить иерархически, в соответствии с тем, как вы к ним относитесть: на первом месте среди позитивных — самую дорогую для вас Ценность, на втором месте — пости самую дорогую, и так далее. Негативные Ценности: на последнем месте самое неприятное и нежеланное, на предпоследнем — почти самое неприятное/нежеланное, и так далее. Нейтральные ценнсти сортировать не нужно — их порядок не имеет значения.

Эта задача может потребовать длительных размышлений. Желательно принять решение тогда, когда сможете выбрать две самые желанные и две самые нежеланные Ценности. Хотя Ценности можно распределить как угодно — и все решения будут учтены — наибольший "вес" будут иметь две первые позитивные и две последние негативные Ценности. (Здесь я предполагаю, что в большинстве случаев у человека есть по крайней мере 2 позитивных и 2 негативных ценности, и эти ценности являются решающими.)
Ценностный профиль можно будет изменить позже, но частые изменения понизят шансы найти друзей.

На третьем этапе выберете утверждение, которое характеризует ваше отношение к ценностям в целом.