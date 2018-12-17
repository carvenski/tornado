

# tornado其实一切都是基于python的原生yield的效果来实现的,tornado的@coroutine装饰器封装了原生的generator生成器,替你调用了它的send等方法来执行协程
# 并重点使用一个future对象来在协程和loop调度者之间交互.

res = yield some_coroutine_function()  
等价于
future = some_coroutine_function()  
res = yield future 

future = some_coroutine_function()  这一句会 ·开启协程· 并返回一个future对象（这都是靠着tornado的@coroutine装饰器内部实现的效果）
res = yield future 而这一句只是单纯的使用了python的原生yield的效果而已：
                   1. 遇到yield处就暂停/挂起当前协程函数, 
                   2. yield后的值(就是某个future)会被返回给当前协程的调用者(loop调度器), 
                   3. yield前的值(就是res结果)会在loop调度器重新回到该协程时一起传进来以供后面顺序逻辑的使用,
                   

以上的解释,基本可以理解tornado的 loop + future + @coroutine 是怎么和 python的原生yield语法/generator生成器 来搭配协作,
来实现 ·多协程调度/协程并发·  以保持CPU一直处于运行状态(所谓的异步非阻塞IO)的了 !!

相信对tornado的底层实现原理的理解学习可以暂告一段落了. 
今年后面时间还是leetcode刷题为主.



