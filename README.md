The Likes, backend.
===========================================

The Likes is an app designed to find people with the same personal values. More detailed explanation below (also in Russian).

#### Tools used:
- Python 3.12
- Fastapi 0.116.1
- Fastapi-users 14.0.1
- Sqlalchemy 2.0.41
- Alembic 1.16.4
- PostgreSQL 17


Documentation files - documentation.yaml, documentation.json - in root folder.
To read - upload any to https://editor.swagger.io/

#### To run:

Install and run PostgreSQL 17.
Create new database.

Install PostGIS extension
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Clone project
```shell
git clone git@github.com:hkkmrmnq/the_likes.git
```

Go to directory
```shell
cd the_likes
```

Install environment with dependencies
```shell
uv sync
```

Create .env file with
```
PG_USER=...  # name of your postgres user
PG_PASSWORD=...  # your postgres password
PG_HOST=...   # your postgres host
PG_PORT=...  # your postgres port
PG_DB_NAME=...  # name of your postgres database
JWT_SECRET=...   # create a secret key that will be used by JWT
JWT_REFRESH_LIFETIME=...  # choose your values in seconds
RESET_PASSWORD_TOKEN_SECRET=...  # create a secret key that will be used by FastAPI Users
VERIFICATION_TOKEN_SECRET=  # create a secret key that will be used by FastAPI Users
EMAIL_APP_EMAIL=...  # optional, google config (currently info is printed out)
EMAIL_APP_NAME=...  # optional, google config (currently info is printed out)
EMAIL_APP_PASSWORD=...  # optional, google config (currently info is printed out)
```

Run migrations
```shell
uv run alembic upgrade head
```

Populate database with core data
```shell
uv run py prepare.py data
```

Optional, add superuser
```shell
uv run py prepare.py superuser
```

Run app
```shell
uv run fastapi dev src/main.py
```

Access documrntation: http://127.0.0.1:8000/docs#/





# Introduction for users

[Russian version](#введение-для-пользователей)


The project is primarily aimed at people who feel a lack of social connections and would like to find new friends, but are tired of failing to do so. Many are familiar with the term "alienation" — perhaps it's a suitable name for the problem I hope to help some people solve. I don't insist on using this term, but I use it for convenience.

There are many opinions and approaches to solving the problem of alienation. I proceed from the following assumption.
1. Friendship begins and is maintained not by logic, but by emotion. We can be friends with someone who doesn't share our values — and not notice it amidst the positive emotions.
2. Historically, over time, whether due to technological advancement, the spread of education, or other reasons, people have become increasingly rational — relying less on emotions and more on logic, analysis, strategy, and so on. Therefore, friendship is becoming increasingly rare, and this is most relevant for people who do not share the value system of the majority.
3. I don't think the process of rationalization can be stopped. If we want to preserve friendship, we must learn to begin new relationships not with emotion, but on rational grounds.

If successful, this project should become a rational push for the beginning of new, long—term, and strong relationships.
To do this, I propose defining your values — and based on this, the algorithm will select participants with similar values.
Different people often attach different meanings to the same words. Therefore, I suggest you not only choose values ​​that are close to yours, but also choose the meanings you attach to these terms.

I should warn you right away that, due to this approach, finding suitable users may take quite a while — and will certainly take time in the early stages, until a sufficient number of users have been recruited. I hope this won't discourage you.

If you want to know the reasons behind the choice of terms denoting values, here is the position from which I follow:

1. Reality exists independently of us and is knowable through experience. It can be understood as a set of all possible descriptive statements that denote either the very fact of our experience, or logically necessarily follow from the totality of facts.
2. Another type of statements are evaluative. We make evaluative statements — primarily mentally — about what we think reality should be like. Evaluative statements can take forms such as "X is good/bad, right/wrong" and "X should/should not be done".
3. Along with this, there is the concept of "moral values" — something like guidelines, relying on which we make evaluative statements.
4. Descriptive statements are logically connected with facts. Evaluative statements are also logically connected with moral values.
5. Further, I will use the term "values" in the following meaning. Values ​​are terms that:
— are extremely abstract (for example, "love", "beauty" — these concepts themselves cannot act as concrete/particular in relation to some more abstract concept — so that the meaning of the concepts "love" and "beauty" does not was partially or completely lost);
— work as moral guidelines (actions, words, thoughts, decisions, behavior of any person — will always to some extent be directed towards/from "love", "beauty", etc.);
— are ultimately unattainable, but they can be pursued infinitely effectively (it is impossible to find all possible love in the universe/reality/existence, but love can be infinitely multiplied);
— are neutral in themselves, until they are organized into a hierarchy (love in itself is neither good nor bad — we ourselves choose to what extent to strive for it / from it — and only this choice creates a hierarchy — places love above/below other moral values).
6. A) Each person has an internal hierarchy of values, which influences his emotions, thoughts, language, decisions and behavior, etc. B) Even if there is no such internal hierarchy — every thought, word and action of each person influences the world around, changing it in a certain way way — as if shifting (even if only a little) in a certain direction. In some directions a person moves (and moves the world) more often, in some — less often. The set of these directions is the same as an internal hierarchy of values.
Thus, ideas A and B are interchangeable in the context of reasoning about what (abstract moral) values ​​are.
7. A personal hierarchy of values ​​is not directly accessible to either oneself or others. We can try to express it in thoughts, words, actions, or any other means, but there is no way to test a person's values. I will conditionally assume that each person has one hierarchy of moral values, which is guided by his unconscious (or it is simply a set of all previous chocies/decisions/acts/etc), and another — conscious — the one that, conditionally, arises at the moment when a person consciously decides to pursue certain moral guidelines. How similar are the unconscious and conscious value systems of a particular person is a question that is unlikely to be answered.
8. I assume that The unconscious hierarchy of values ​​can be changed through long—term conscious effort — through self—analysis and, most importantly, through discussion with people who chose similar values.


# Instructions for users

I offer you a set of terms denoting possible abstract values: Pleasure, Comfort, Happiness, Love, Beauty, Wealth, Status, Power, Violence, Truth, Freedom.

In the first step, you must select components (or subdefinitions) — Aspects — for each value. If you agree that a statement should be included in the value definition, check the box next to it. For example, if you agree that Beauty is (partially or completely) an objective quality, include this aspect in the definition of beauty.

Choose your Aspects carefully. Each combination of Aspects is considered by the algorithm as an independent Value. That is, if you included the Aspect "objective quality" in Beauty, and someone else included all the same Aspects as you, but did not include "objective quality," we do not know how close or distant these two concepts are. Therefore, your Beauty and the Beauty of that other person are considered by the algorithm as Two completely different values ​​(despite the same name – Beauty).

In the second step, distribute the Values ​​among three groups: positive, negative, and neutral. Initially, all Values ​​are in the neutral group. If, for example, you want more Beauty in reality, move it to the positive group. If, conversely, you believe there should be less Beauty, move it to the negative group. If you want neither more nor less Beauty, leave it in the neutral group. Distribute all Values ​​according to this principle.

Positive and negative Values ​​should be arranged hierarchically, according to how you feel about them: in first place among the positive ("good") — the Value most dear to you, in second place is the next most dear, and so on. Negative Values ​​(anti—values, "bad"): in last place is the most unpleasant and undesirable, in second to last is the almost most unpleasant/undesirable, and so on. Neutral values ​​do not need to be sorted — their order doesn't matter.

I expect this task will require considerable deliberation. Perhaps days, months... It's best to make a decision when you can identify the two most desired and two least desired values. Thougр the values ​​can be ordered any way you like — the algorithm takes all decisions into account — preference will be given to the first two positive and last two values. (Here, I'm assuming that in most cases a person have at least 2 positive and two negative values, and 2 most positive and 2 most negative values are most decisive.)
You can change your value profile later, but frequent changes will reduce your chances of making friends.

In the third step, you'll choose a statement that characterizes your overall attitude toward values.


# Введение для пользователей

Проект ориентирован, прежде всего, на людей, которые ощущают нехватку социальных связей и хотели бы найти новых друзей, но устали от неудач в этих попытках. Многие знакомы с термином "отчуждение" — возможно, он подходит для названия той проблемы, которую я надеюсь помочь решить какому—то количеству людей. Не отдаю предпочтение именно этому термину, но использую его для удобства.

Есть много мнений и подходов к решению проблемы отчуждения. Я же исхожу из слкдующего предположения.
1. Дружба начинается и поддерживается не логикой, а эмоциями. Мы можем дружить с человеком, который не разделяет наших ценностей — и не замечать этого на фоне положительных эмоций.
2. Исторически, с течением времени, в силу ли технического развития, распространения образования, или в силу ещё каких—то причин, — люди становятся всё более рациональными — всё меньше полагаются на эмоции, и всё больше — на логику, анализ, статегию и т.п. Поэтому дружба становится всё более редким явлением, и это наиболее актуально для людей, не разделяющих систему ценностей большинства.
3. Не думаю, что процесс рационализации может быть остановлен. Если мы хотим сохранить дружбу, то должны учиться начинать новые отношения не с помощью эмоций, а на рациональных основаниях.

В случае успеха, этот проект должен стать таким рациональным толчком для начала новых длительных и крепких отношений.
Для этого предлагаю определить ваши ценности — и на основе этого алгоритм подберёт участников с близкими вам ценностями.
Нередко разные люди вкладывают разный смысл в одни и те же слова. Поэтому я предлагаю вам не только выбрать ценности, близкие вашим, но и выбрать те смыслы, которые вы вкладываете в эти термины.

Сразу предупрежу, что, в связи с таким подходом, поиск подходящих пользователей может занять довольно продолжительное время — и наверняка займёт на раннем этапе — пока не наберётся достаточное количество пользователей. Надеюсь, это вас не отпугнёт.

Если вы хотите узнать, чем обусловлен выбор терминов, обозначающих ценности — вот позиция, из которой я исхожу:

1. Реальность существует независимо от нас и познаваема посредством опыта. Её можно понимать как совокупность всех возможных описательных утверждений, которые обозначают либо сам факт нашего опыта, либо логически необходимо следуют из всей совокупности фактов.
2. Ещё один тип утверждений — оценочные. Мы делаем оценочные утверждения — в первую очередь мысленно — о том, какой, по нашему мнению, должна быть реальность. Оценочные утверждения могут иметь такие формы, как «X — это хорошо/плохо, правильно/неправильно» и «следует / не следует сделать X».
3. Вместе с этим существует понятие "моральные ценности" — нечто, вроде ориентиров, опираясь на которые мы и делаем оценочные утверждения.
4. Описательные утверждения логически связаны с фактами. Оценочные утверждения — так же логически — связаны с моральными ценностями.
5. Далее я буду употреблять термин "ценности" в следующем значении. Ценности — это термины, которые:
— предельно абстрактны (например, "любовь", "красота" — эти понятия сами не могут выступать как конкретные/частные по отношению к какому—то более абстрактному понятию — так, чтобы смысл понятий "любовь" и "красота" не был частично или полностью утерян);
— работают как моральные ориентиры (действия, слова, мысли, решения, поведение любого человека — всегда в какой—то степени будут направлены к/от "любви", "красоты" и т.п.);
— финально не достижимы, но их можно бесконечно эффективно преследовать (невозможно обрести всю возможную любовь во вселенной/реальности/бытии, но любовь можно бесконечно приумножать);
— нейтральны сами по себе, пока не организованы в иерархию (любовь сама по себе — ни хорошая, ни плохая — мы сами выбираем, в какой степени стремиться к ней / от неё — и только этот выбор создаёт иерархию — помещает любовь выше/ниже других моральных ценностей).
6. А) У каждого человека есть внутренняя иерархия ценностей, которая оказывает влияние на его эмоции, мысли, язык, решения и поведение и т.д. Б) Даже если такой внутренней иерархии нет — каждая мысль, слово и действие каждого человека оказывает влияние на мир вокруг, изменяя его определённым образом — как—бы смещая (даже если совсем немного) в определённом направлении. В каких—то направлениях человек двигается (и двигает мир) чаще, в каких—то — реже. Набор этих направлений — то же самое, что внутренняя иерархия ценностей.
Таким образом, представления А и Б взаимозаменяемы в контексте рассуждения о том, что такое (абстрактные моральные) ценности.
7. Персональная иерархия ценностей недоступна напрямую ни себе, ни другим. Мы можем попытаться выразить её в мыслях, словами, действиями, или любыми другими средствами, но не существует способа проверить ценности человека. Условно предположу, что у каждого человека есть одна иерархия моральных ценностей, которой руководствуется его бессознательное (или же это просто совокупность всех предыдущих выборов/решений/действий и т.д.), и другая — сознательная — та, которая, условно, возникает в момент, когда человек сознательно решает преследовать определённые моральные ориентиры. Насколько схожи бессознательная и сознательная системы ценностей у какого—то конкретного человека — это вопрос, на который вряд ли возможен ответ.
8. Я предполагаю, что бессознательную иерархию ценностей можно изменить с помощью длительных сознательных усилий — через самоанализ и, что особенно важно, через обсуждение с людьми, имеющими схожие ценности.


# Инструкция для пользователей

Предлагаю вам набор терминов, означающих возможные абстрактные ценности: Удовольствие, Комфорт, Счастье, Любовь, Красота, Богатство, Статус, Власть, Насилие, Истина, Свобода.

На первом этапе для каждой ценности необходимо выбрать составляющие (или подопределения) — Аспекты. Если вы согласны с тем, что утверждение должно быть включено в определение ценности, — поставьте галочку рядом с ним. Например, если вы согласны, что Красота — это (частично или полностью) объективное качество — включите этот аспект в опредение красоты.

Внимательно выбирайте Аспекты. Каждая комбинация Аспектов рассматривается алгоритмом как самостоятельная Ценность. То есть, если вы включили Аспект "объективное качество" в Красоту, а кто—то другой включил в Красоту все те же Аспекты, что и вы, но не включил "объективное качество" — мы не знаем, насколько близки или далеки эти два понятия. Поэтому, ваша Красота, и Красота того второго человека рассматриваются алгоритмом как две совершенно разные ценнсти (несмотря на одинаковое название — Красота).


На втором этапе распределите Цености между тремя группами: позитивные, негативные и нейтральные. Вначале все Ценности находятся в нейтральной группе. Если, например, вы хотите, чтобы в реальности было больше Красоты, — переместите её в группу положительных. Если, наоборот, считаете, что Красоты должно быть меньше — переместите в группу негативных. Если же не хотите ни больше, ни меньше Красоты — оставьте её в нейтральной группе. По такому принципу распределите все Ценности.

Позитивные и негативные Ценности нужно располжить иерархически, в соответствии с тем, как вы к ним относитесть: на первом месте среди положительных ("хорошее") — самую дорогую для вас Ценность, на втором месте — пости самую дорогую, и так далее. Негативные Ценности (ати—ценности, "плохое"): на последнем месте самое неприятное и нежеланное, на предпоследнем — почти самое неприятное/нежеланное, и так далее. Нейтральные ценнсти сортировать не нужно — их порядок не имеет значения.

Предположу, что эта задача потребует длительных размышлений. Возможно, дни, месяцы... Желательно принять решение тогда, когда сможете выбрать две самые желанные и две самые нежеланные Ценности. Хотя Ценности можно распределить как угодно — алгоритм учитывает все решения — предпочтение будет отдано двум первым и двум последним Ценностям. (Здесь я предполагаю, что в большинстве случаев у человека есть по крайней мере 2 положительных и 2 отрицательных ценности, и 2 самых положительных и 2 самых отрицательных ценности являются наиболее решающими.)
Ценностный профиль можно будет изменить позже, но частые изменения понизят шансы найти друзей.

На третьем этапе выберете утверждение, которое характеризует ваше отношение к ценностям в целом.