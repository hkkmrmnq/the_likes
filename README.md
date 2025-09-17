Backend for The Likes app. Work in progress.
===========================================

The Likes is an app designed to find people with the same personal values. More detailed explanation further down below.

#### Tools used:
- Python 3.12
- Fastapi 0.116.1
- Fastapi-users 14.0.1
- Sqlalchemy 2.0.41
- Alembic 1.16.4
- PostgreSQL 17


Documentation files - docs.yaml, docs.json - in root folder.
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

Activate environvent
```shell
.venv/scripts/activate
```

Create .env file with
```
PG_USER=...  # name of your postgres user
PG_PASSWORD=...  # your postgres password
PG_HOST=...   # your postgres host
PG_PORT=...  # your postgres port
PG_DB_NAME=...  # name of your postgres database
JWT_SECRET=...   # create a secret key that will be used by JWT
JWT_ACCESS_LIFETIME=...  # choose your values in seconds
JWT_REFRESH_LIFETIME=...  # choose your values in seconds
RESET_PASSWORD_TOKEN_SECRET=...  # create a secret key that will be used by FastAPI Users
VERIFICATION_TOKEN_SECRET=  # create a secret key that will be used by FastAPI Users
EMAIL_APP_EMAIL=...  # optional, google config (currently info is printed out)
EMAIL_APP_NAME=...  # optional, google config (currently info is printed out)
EMAIL_APP_PASSWORD=...  # optional, google config (currently info is printed out)
```

Run migrations
```shell
alembic upgrade head
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





Introduction for users
===========================================

The idea of ​​the project is to give you the opportunity to choose values ​​that are close to your own and introduce you to new people who have similar values.
However, different people often put different meanings into the same words. Therefore, I suggest that you not only choose values ​​that are close to yours, but also choose the meanings that you put into these terms.
The project is aimed primarily at people who do not feel like they "fit in" in society, but would like to find new friends. I will warn you right away that, due to this approach, finding suitable users can take quite a long time (and will certainly take up on early stage - until there is a sufficient number of different users). I hope this will not scare you off.

If you want to know in more detail why the project is structured this way - below is the position from which I proceed.

1. Reality exists independently of us and is knowable through experience. It can be understood as a set of all possible descriptive statements that denote either the very fact of our experience, or logically necessarily follow from the totality of facts.
2. Another type of statements are evaluative. We make evaluative statements - primarily mentally - about what we think reality should be like. Evaluative statements can take forms such as "X is good/bad, right/wrong" and "X should/should not be done".
3. Along with this, there is the concept of "moral values" - something like guidelines, relying on which we make evaluative statements.
4. Descriptive statements are logically connected with facts. Evaluative statements are also logically connected with moral values.
5. Further, I will use the term "values" in the following meaning. Values ​​are terms that:
- are extremely abstract (for example, "love", "beauty" - these concepts themselves cannot act as concrete/particular in relation to some more abstract concept - so that the meaning of the concepts "love" and "beauty" does not was partially or completely lost);
- work as moral guidelines (actions, words, thoughts, decisions, behavior of any person - will always to some extent be directed towards/from "love", "beauty", etc.);
- are ultimately unattainable, but they can be pursued infinitely effectively (it is impossible to find all possible love in the universe/reality/existence, but love can be infinitely multiplied);
- are neutral in themselves, until they are organized into a hierarchy (love in itself is neither good nor bad - we ourselves choose to what extent to strive for it / from it - and only this choice creates a hierarchy - places love above/below other moral values).
6. A) Each person has an internal hierarchy of values, which influences his emotions, thoughts, language, decisions and behavior, etc. B) Even if there is no such internal hierarchy - every thought, word and action of each person influences the world around, changing it in a certain way way - as if shifting (even if only a little) in a certain direction. In some directions a person moves (and moves the world) more often, in some - less often. The set of these directions is the same as an internal hierarchy of values.
Thus, ideas A and B are interchangeable in the context of reasoning about what (abstract moral) values ​​are.
7. A personal hierarchy of values ​​is not directly accessible to either oneself or others. We can try to express it in thoughts, words, actions, or any other means, but there is no way to test a person's values. I will conditionally assume that each person has one hierarchy of moral values, which is guided by his unconscious (or it is simply a set of all previous chocies/decisions/acts/etc), and another - conscious - the one that, conditionally, arises at the moment when a person consciously decides to pursue certain moral guidelines. How similar are the unconscious and conscious value systems of a particular person is a question that is unlikely to be answered.
8. I assume that The unconscious hierarchy of values ​​can be changed through long-term conscious effort - through self-analysis and, most importantly, through discussion with people who chose similar values.