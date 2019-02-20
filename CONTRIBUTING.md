## Contributing

First off, thank you for considering contributing to Micro-Tiling. It's people like you that make Micro-Tiling such a great tool.

### Where do I go from here?

If you've noticed a bug or have a question, [search the issue tracker][] to see if someone else in the community has already created a ticket. If not, go ahead and [make one][new issue]!

### Fork & create a branch

If this is something you think you can fix, then [fork Micro-Tiling](https://help.github.com/articles/fork-a-repo) and create a branch with a descriptive name.

A good branch name would be (where issue #325 is the ticket you're working on):

```
git checkout -b 325-add-japanese-translations
```

### Get the test suite running

TODO

### Did you find a bug?

* **Ensure the bug was not already reported** by [searching all issues][].

* If you're unable to find an open issue addressing the problem, [open a new one][new issue]. Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

### Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first :smile_cat:

### Get the style right

Your patch should follow the same conventions & pass the same code quality checks as the rest of the project.

### Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with Micro-Tiling's master branch:

```sh
git remote add upstream git@github.com:traxys/micro-tiling.git
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```sh
git checkout 325-add-japanese-translations
git rebase master
git push --set-upstream origin 325-add-japanese-translations
```

Finally, go to GitHub and [make a Pull Request][] :D

Travis CI will run our test suite. We care about quality, so your PR won't be merged until all tests pass.

### Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

To learn more about rebasing in Git, there are a lot of [good][git rebasing] [resources][interactive rebase] but here's the suggested workflow:

```sh
git checkout 325-add-japanese-translations
git pull --rebase upstream master
git push --force-with-lease 325-add-japanese-translations
```
