"use client";

import { useEffect } from "react";
import { useLoadingStore } from "@/src/stores";
import { Header } from "@/src/components";

export default function AboutPage() {
  const { stopLoading } = useLoadingStore();
  useEffect(() => {
    stopLoading();
  }, [stopLoading]);
  return (
    <div className="flex flex-col h-screen">
      <header className="h-16 flex-shrink-0">
        <Header />
      </header>
      <main className="flex-1 overflow-auto thin-scrollbar">
        <div className="flex justify-center">
          <div className="p-2 max-w-[800px]">
            <p>
              The Likes is an application for finding people with same values.
            </p>
            <p>I proceed from the following assumption.</p>
            <ol>
              <li>
                1. Friendship begins and is maintained not by logic, but by
                emotion. We can be friends with someone who doesn't share our
                values — and not notice it amidst the positive emotions.
              </li>
              <li>
                2. Over time (due to technological development, the spread of
                education, or some other reasons), people become more rational —
                relying less on emotions and more on logic, analysis, strategy,
                etc. This makes it more difficult for them to make new friends.
              </li>
              <li>
                3. I don't think the process of rationalization can be stopped.
                If we want to preserve friendship, we must learn to begin new
                relationships not with emotion, but on rational grounds —
                personal values.
              </li>
            </ol>
            <p>
              If successful, this project should become a push for the beginning
              of new, long—term, and strong relationships. To do this, I propose
              defining your values — and based on this, the algorithm will
              select similar participants.
            </p>
            <p>
              Since, as a rule, different people put different meanings into the
              same words, I suggest you not only choose values that are close to
              yours, but also choose the meanings that you put into these terms.
            </p>
            <p>
              Due to this approach, finding suitable users may take quite a
              while — especially in the early stages, until a sufficient number
              of users participate. I hope this won't discourage you.
            </p>
            <p>
              If you want to know the reasons behind the choice of terms
              denoting values, here is the position from which I follow:
            </p>

            <ol>
              <li>
                1. Reality exists independently of us and is knowable through
                experience. It can be understood as a set of all possible
                descriptive statements that denote either the very fact of our
                experience, or logically necessarily follow from the totality of
                facts.
              </li>
              <li>
                2. Another type of statements are evaluative. We make evaluative
                statements about what we think reality should be like.
                Evaluative statements can take forms such as X is good/bad,
                right/wrong; and X should/should not be done.
              </li>
              <li>
                3. Along with this, there is the concept of moral values —
                something like guidelines, relying on which we make evaluative
                statements.
              </li>
              <li>
                4. Descriptive statements are logically connected with facts.
                Evaluative statements are also logically connected with moral
                values.
              </li>
              <li>
                5. Further, I will use the term "values" in the following
                meaning. Values are terms that:
                <ul>
                  <li>• are highly abstract;</li>
                  <li>
                    • work as moral guidelines (actions, words, thoughts,
                    decisions, behavior of any person — will always to some
                    extent be directed towards/from some kind of
                    love/beauty/etc.);
                  </li>
                  <li>
                    • are ultimately unattainable, but can be pursued infinitely
                    effectively (it is impossible to find all possible love in
                    the universe, but we always can find more love);
                  </li>
                  <li>
                    • are neutral in themselves, until they are organized into a
                    hierarchy (love in itself is neither good nor bad — we
                    ourselves choose to what extent to strive for it / from it —
                    and only this choice creates a hierarchy — places love
                    above/below other moral values).
                  </li>
                </ul>
              </li>
              <li>
                6.
                <ol>
                  <li>
                    6.1. Each person has an internal hierarchy of values, which
                    influences his emotions, thoughts, language, decisions and
                    behavior, etc. And / or:
                  </li>
                  <li>
                    6.2. Every thought, word and action of each person
                    influences the world in a certain way — as if shifting (even
                    if only a little) in a certain direction. In some directions
                    a person moves (and moves the world) more often, in some
                    directions — less often.
                  </li>
                  <li>
                    6.3. Statements 6.1 and 6.2 are interchangeable in the
                    context of reasoning about what (abstract moral) values are:
                    the set of directions and their "weights" is the same as an
                    internal hierarchy of values.
                  </li>
                </ol>
              </li>
              <li>
                7. Personal hierarchy of values is not directly accessible to
                consciousness.
              </li>
              <li>
                8. When attempting to define (or choose) a hierarchy of one's
                values, a second (conscious) hierarchy of values is created in
                addition to the first (real) one. How similar the real and
                conscious value hierarchies will be for any given person is a
                question that is hardly possible to answer.
              </li>
              <li>
                9. Since the real/unconscious is not completely isolated from
                the conscious, I propose that the unconscious value hierarchy
                can be changed through sustained conscious effort — through
                self-analysis and, most importantly, through discussion with
                people who share similar values.
              </li>
            </ol>
            <p>Therefore, despite the obstacles, I propose this approach.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
