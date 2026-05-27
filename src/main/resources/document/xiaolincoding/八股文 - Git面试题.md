# 小林coding - Git面试题
---
## Git 面试题
---
## Git 使用熟练吗？
熟悉，项目的代码是用 git 工具来管理的/
git 的工作原理如下图：
几个专用名词的译名如下：
- Workspace：工作区
- Index / Stage：暂存区
- Repository：仓库区（或本地仓库）
- Remote：远程仓库
工作流程
最基础的工作流程，首先执行git pull获取远程仓库的最新代码，进行代码的编写。
完成相应功能的开发后执行git add .将工作区代码的修改添加到暂存区，再执行git commit -m 完成xx功能将暂存区代码提交到本地仓库并添加相应的注释，最后执行git push命令推送到远程仓库。
撤回 git commit 操作
当执行了git commit -m 注释内容命令想要撤回，可以使用git reset --soft HEAD^把本地仓库回退到当前版本的上一个版本，也就是刚刚还没提交的时候，代码的改动会保留在暂存区和工作区。
也可以使用git reset --mixed HEAD^，这样不止回退了刚刚的git commit操作，还回退了git add操作，代码的改动只会保留在工作区。因为--mixed参数是git reset命令的默认选项，也就是可以写为git reset HEAD^。
撤回 git push 操作
当执行了git push命令想要撤回，可以使用git reset HEAD^将本地仓库回退到当前版本的上一个版本，代码的修改会保留在工作区，然后使用git push origin xxx --force将本地仓库当前版本的代码强制推送到远程仓库。
---
## git rebase和merge的区别
- Rebase（变基）是将一个分支上的提交逐个地应用到另一个分支上，使得提交历史变得更加线性。当执行rebase时，Git会将目标分支与源分支的共同祖先以来的所有提交挪到目标分支的最新位置。这个过程可以看作是将源分支上的每个提交复制到目标分支上。简而言之，rebase可以将提交按照时间顺序线性排列。
- Merge（合并）是将两个分支上的代码提交历史合并为一个新的提交。在执行merge时，Git会创建一个新的合并提交，将两个分支的提交历史连接在一起。这样，两个分支的修改都会包含在一个合并提交中。合并后的历史会保留每个分支的提交记录。
---
## 如何使用 git 命令合并两个分支，发生冲突如何解决
- 查看冲突：当发生冲突时，Git 会提示您文件中的冲突部分。您可以使用以下命令查看所有冲突文件的状态。
```
git status
```
- 解决冲突：打开包含冲突的文件，您会看到类似以下的标记：
```
<<<<<<< HEAD
// 代码来自目标分支
=======
// 代码来自要合并的分支
>>>>>>> branchName
```
您需要手动编辑这些文件，决定保留哪些变更或者如何整合这些变更。
- 标记为已解决：完成冲突解决后，对已解决的文件使用以下命令标记为已解决。
```
git add <已解决文件>
```
- 完成合并：继续提交这些已解决的冲突文件。
```
git commit -m "解决合并冲突"
```
---
## Git 有哪几个工作区域？它们之间是怎么流转的？
Git 内部主要有四个区域：
- 工作区（Workspace）：本地磁盘上你能直接看到和修改的项目目录。
- 暂存区（Index / Stage）：git add之后文件的快照会被暂存在.git/index里。
- 本地仓库（Local Repository）：git commit之后，暂存区的内容被固化成一条 commit，记录到本地的.git目录。
- 远程仓库（Remote Repository）：托管在 GitHub、GitLab 等远程服务器上的仓库，git push把本地 commit 同步过去。
正向数据流：工作区 --git add--> 暂存区 --git commit--> 本地仓库 --git push--> 远程仓库
反向数据流：远程仓库 --git fetch/pull--> 本地仓库 --git checkout/restore--> 工作区
理解这四个区域是理解git reset、git stash、git diff的基础。
---
## git pull和git fetch有什么区别？
- git fetch：只把远程仓库的最新 commit 拉到本地的远程跟踪分支（比如origin/main），不会改动当前工作区和本地分支，相当于只"下载"。拉下来之后你可以先git log origin/main看看远程都改了什么，再决定要不要合并。
- git pull：等价于git fetch + git merge FETCH_HEAD，先拉取远程更新，然后立刻合并到当前分支。
日常开发中推荐先git fetch看一眼再手动选择merge还是rebase，这样可以避免被意外的远程改动拉出 merge commit 或冲突。
---
## git diff有哪些常见用法？
git diff是万能的"差异查看"命令，根据对比对象不同有多种模式：
- git diff：工作区 vs 暂存区（还没add的修改）
- git diff --cached/git diff --staged：暂存区 vs HEAD（已经add但还没commit的修改）
- git diff HEAD：工作区 vs HEAD（工作区所有未 commit 的修改，最常用）
- git diff main feat/a：两个分支之间的差异
- git diff commit1 commit2：两个 commit 之间的差异
- git diff main feat/a -- <file>：指定文件的差异
记住一个口诀：默认对比工作区，--cached对比暂存区。
---
## 什么是 HEAD？什么是游离 HEAD（detached HEAD）？
- HEAD是一个特殊的指针，正常情况下指向"当前分支的最新 commit"。更准确地说，它通常指向一个分支引用（如refs/heads/main），然后这个分支再指向具体的 commit。
- 游离 HEAD（detached HEAD）：当你执行git checkout <commit-hash>或git checkout <tag>时，HEAD 会直接指向一个 commit 而不是分支。这时你做的新 commit 不属于任何分支，一旦git switch切走，这些 commit 就可能被垃圾回收而丢失。
如果你在 detached HEAD 状态下做了重要修改，一定要git switch -c new-branch创建一个新分支把它们保存下来。
---
## git reset的--soft、--mixed、--hard三种模式有什么区别？
三个参数决定了 reset 对本地仓库 HEAD、暂存区、工作区三个区域的影响范围：
| 模式 | 本地仓库 HEAD | 暂存区 | 工作区 |
| --- | --- | --- | --- |
| --soft | ✅ 回退 | ❌ 保留 | ❌ 保留 |
| --mixed（默认） | ✅ 回退 | ✅ 回退 | ❌ 保留 |
| --hard | ✅ 回退 | ✅ 回退 | ✅ 回退 |
- --soft：相当于"只撤销 commit、保留 add"，修改还在暂存区，可以直接重新 commit。适合想重写最近一次 commit 内容时用。
- --mixed：相当于"撤销 commit 和 add"，修改还在工作区，需要重新add + commit。这是默认行为。
- --hard：相当于"撤销一切"，工作区也会被清空，最危险，没 commit 或 stash 的改动会直接丢失。只在确认不需要本地所有改动时才用。
---
## git reset和git revert的区别是什么？
- git reset <commit>：把 HEAD 指针往回移动到指定 commit，后面的 commit 会"消失"，本质是改写历史。不适合已经 push 到共享远程的 commit，否则会和其他人的本地历史冲突。
- git revert <commit>：生成一条新的commit，这条新 commit 的内容正好是指定 commit 的反向（undo），原来的 commit 依然保留在历史中，不会改写历史。安全，适合在共享分支上回滚已发布的改动。
简单口诀：reset 是"把时间倒回去"，revert 是"走一步后退的步子"。共享分支永远优先用 revert。
---
## git commit --amend是做什么的？什么时候用？
git commit --amend用于修改最近一次 commit，最常见的两种用法：
- 只改提交信息：git commit --amend -m "新的提交信息"
- 补提交漏掉的文件：先git add <file>，再git commit --amend --no-edit
需要注意的是，amend 实际上是生成了一个新的 commit（hash 会变），替换掉原来的那个。所以如果原 commit 已经 push 到远程并被别人拉过，不要 amend，否则会让别人的本地历史对不上。对已推送的 commit 改完后必须git push --force-with-lease（比--force更安全，因为它会检查远程有没有被别人推过新 commit）。
---
## git checkout、git switch、git restore有什么关系？
在 Git 2.23 之前，git checkout一个命令同时承担了两个完全不同的职责：切换分支和恢复文件。这种"一词多义"容易把新手绕晕。Git 2.23（2019 年发布）引入了两个新命令把职责拆开：
- git switch：专门用于切换分支git switch main：切到main分支git switch -c feat/xxx：创建并切换到新分支
- git switch main：切到main分支
- git switch -c feat/xxx：创建并切换到新分支
- git restore：专门用于恢复文件git restore <file>：撤销工作区修改（恢复到暂存区或 HEAD 的版本）git restore --staged <file>：把文件从暂存区撤回工作区（等价于老的git reset HEAD <file>）
- git restore <file>：撤销工作区修改（恢复到暂存区或 HEAD 的版本）
- git restore --staged <file>：把文件从暂存区撤回工作区（等价于老的git reset HEAD <file>）
git checkout仍然可用，但现代项目推荐按职责用switch和restore，语义更清晰。
---
## git stash是做什么用的？常用命令有哪些？
git stash用于临时保存当前工作区的修改，让你可以切去别的分支或做别的事情，等会儿再回来继续。
典型场景：你在feat/a分支改了一半代码还没 commit，这时main分支突然要紧急修 bug，你就可以git stash把当前修改暂存起来，切到main修完 bug 后，再git stash pop把之前的改动取回来继续干。
常用命令：
- git stash/git stash push -m "msg"：暂存当前修改
- git stash list：查看所有 stash
- git stash pop：弹出最近一次 stash 并应用到工作区（取出后从 stash 栈删除）
- git stash apply：应用某个 stash 但不删除它（可以反复 apply）
- git stash drop：丢弃某个 stash
- git stash clear：清空所有 stash
stash 是本地栈结构，默认不会推到远程。
---
## 不小心把敏感信息（密码、密钥）提交到 Git 怎么办？
首先要明确一点：仅仅git reset或git revert是不够的，因为 commit 历史里还残留着敏感信息，只要 clone 下来就能看到。必须从 Git 历史中彻底清除：
- 如果还没 push：直接git reset --hard <上一个干净的 commit>，然后重新 add/commit/push 即可。
- 如果已经 push：需要改写历史旧方法：git filter-branch（慢、难用，官方已不推荐）推荐方式：用git filter-repo或BFG Repo-Cleaner工具，批量清理指定字符串或指定文件清理完后必须git push --force --all强推覆盖远程，并让所有协作者重新 clone
- 旧方法：git filter-branch（慢、难用，官方已不推荐）
- 推荐方式：用git filter-repo或BFG Repo-Cleaner工具，批量清理指定字符串或指定文件
- 清理完后必须git push --force --all强推覆盖远程，并让所有协作者重新 clone
但最重要的是：一旦密钥/密码被推送到公网仓库，就应该假设它已经泄露——爬虫每分钟都在扫 GitHub。所以必须立即去对应的平台（AWS / 数据库 / 第三方 API）作废并轮换密钥，单纯清理 Git 历史远远不够。
---
## git pull和git pull --rebase的区别是什么？
- git pull=fetch + merge，如果你本地和远程都有新 commit，会产生一个额外的 merge commit，让提交历史出现分叉。
- git pull --rebase=fetch + rebase，会把你本地的 commit "搬"到远程分支最新 commit 的后面，保持线性历史，看起来更干净。
在多人协作的长期分支上，推荐用git pull --rebase，可以避免大量无意义的 merge commit 污染历史。很多团队甚至配置git config --global pull.rebase true让 rebase 成为默认行为。
⚠️ 注意：rebase 会改写本地 commit 的 hash，所以不要对已经 push 到远程、被别人拉过的 commit 做 rebase，否则会给协作者带来巨大的历史同步问题。
---
## 什么是 Fast-Forward 合并？和普通 merge 有什么区别？
- Fast-Forward（快进）合并：当目标分支（比如main）和要合并的分支（比如feat/a）之间是直接上下游关系——也就是main从feat/a分出去之后没有新的 commit——Git 只需要把main的指针直接往前挪到feat/a的位置即可，不会产生新的 merge commit，提交历史保持线性。
- Non-Fast-Forward 合并：两个分支有分叉（各自都有新 commit）时，Git 会创建一个新的"merge commit"把两条历史连起来。
可以用git merge --no-ff feat/a强制生成一个 merge commit，即便本来可以 Fast-Forward。这样做的好处是能在历史中清晰看到"这是一次 feature 分支的合并"，很多团队在 feature 合入 main 时会强制加--no-ff，方便回溯和回滚。
---
## git cherry-pick是做什么的？什么场景用？
git cherry-pick <commit>的作用是把某个 commit 的改动"挑"到当前分支，会在当前分支生成一个内容相同的新 commit（hash 不一样）。
典型场景：
- 线上main分支发现一个 bug，你在feat/a分支已经顺手修好了，现在需要把这个修复单独搬到main上，而不是把整个feat/a都合并过去。
- 把某个 hotfix 分支的修复同步回多个长期分支（比如dev、release-1.0）。
常用语法：
- git cherry-pick <commit>：挑一个 commit
- git cherry-pick <c1> <c2> <c3>：挑多个 commit
- git cherry-pick A..B：挑 A（不含）到 B（含）之间的所有 commit
遇到冲突时，手动解决后git add再git cherry-pick --continue，中途想放弃就git cherry-pick --abort。
---
## 如何删除本地分支和远程分支？
删除本地分支：
- git branch -d feat/xxx：安全删除，只有已经合并过的分支才允许删
- git branch -D feat/xxx：强制删除（大写D），未合并的也能删，要小心丢代码
删除远程分支：
- git push origin --delete feat/xxx（推荐写法）
- 或等价写法git push origin :feat/xxx（把"空"推上去，相当于删除）
清理已经在远程被删除但本地还缓存的跟踪分支：
- git fetch --prune或git remote prune origin
这一步容易被忽略，但能解决"git branch -r里一堆早就没了的分支"这种尴尬情况。
---
## 常见的 Git 工作流有哪些？
业界主流有四种：
- Git Flow：有master、develop、feature/*、release/*、hotfix/*多种长期和临时分支，规则严谨，适合版本化发布的产品（比如客户端 App、大型企业产品）。缺点是流程太重，对快速迭代不友好。
- GitHub Flow：只有main一个长期分支 + 多个短生命周期的feature分支，全部通过 Pull Request 合并。简单、灵活，适合持续部署的 Web 应用。
- GitLab Flow：介于两者之间，在 GitHub Flow 的基础上加入了production、pre-production等环境分支，适合需要明确发布环境的场景。
- Trunk-Based Development（主干开发）：所有人直接在main上开发，配合 feature flag 控制功能开关，长分支寿命不超过一两天。需要成熟的 CI/CD 和测试体系，是 Google、Facebook 等大厂主推的模式。
实际上中小团队用得最多的是GitHub Flow或者 Trunk-Based 的变体，Git Flow 现在已经被很多团队认为过时。
---
## Fork、Clone、Pull Request 在 GitHub 协作中分别是什么？
这是开源协作的标准流程，三个概念一定要分清：
- Fork：在 GitHub 上把别人的仓库复制一份到自己的账号下，是服务器端操作。Fork 出的仓库和原仓库保持关联，但你可以自由往自己 fork 的仓库推代码，不影响原作者。
- Clone：把一个远程仓库下载到本地，是本地操作。只有 clone 下来的代码你才能在本地编辑、测试、编译。
- Pull Request（PR）：在自己 fork 的仓库改完代码推上去后，发起一个"请求"，请求原仓库的维护者把你的改动合并进来。原作者可以 review 代码、讨论、最终 merge 或者拒绝。
标准开源贡献流程：
```
Fork（在 GitHub 上）
↓
Clone（到本地）
↓
改代码 + commit
↓
Push 到自己的 Fork
↓
发 Pull Request
↓
维护者 Review & Merge
```
内部团队协作也可以用同样的流程，只不过一般不 fork，而是直接在同一个仓库里建 feature 分支 → 发 PR/MR。
---
## git log常用参数有哪些？
git log本身很朴素，但配合参数能非常强大：
- git log --oneline：一行显示一个 commit，简洁直观
- git log --graph：用 ASCII 图形显示分支 / 合并关系
- git log -n 5：只看最近 5 条
- git log --author="name"：按作者过滤
- git log --since="1 week ago" --until="yesterday"：按时间过滤
- git log --grep="fix"：按 commit message 关键字过滤
- git log -p：显示每个 commit 的完整 diff
- git log --stat：显示每个 commit 修改了哪些文件、增删行数
- git log -- <file>：查看某个文件的修改历史
日常最常用的一个组合：
```
git log --oneline --graph --decorate --all
```
可以在终端里画出完整的分支图，非常好用。可以把它起个别名：git config --global alias.lg "log --oneline --graph --decorate --all"。
---
## git tag有什么用？轻量标签和附注标签有什么区别？
git tag用于给某个 commit 打一个固定的名字（通常是版本号，比如v1.0.0），方便以后找到这个"关键节点"，比如发布版本、里程碑。
两种标签：
- 轻量标签（lightweight tag）：git tag v1.0，只是一个指向 commit 的指针，没有任何额外信息。
- 附注标签（annotated tag）：git tag -a v1.0 -m "release 1.0"，会作为独立的对象存储在 Git 里，包含打标签者、日期、说明、甚至 GPG 签名。
发布版本时应该用附注标签，因为它带有完整的元数据，可追溯性更好；轻量标签更像是一次性的临时书签。
推送标签到远程：
- git push origin v1.0：推送单个
- git push origin --tags：一次推送所有本地标签
删除标签：
- 本地：git tag -d v1.0
- 远程：git push origin --delete v1.0