# ID-Detective

For a exploratory, I tried to create my own service to search people by photos. It was kinda challenge me, and I think I passed it not so bad. In general, I used Python (with Flask and [face_recognition](https://github.com/ageitgey/face_recognition) which is based on [dlib](https://github.com/davisking/dlib)) for converting faces to numbers, MySQL Server 8 for keeping them and searching, [Vk API](https://vk.com/dev/manuals) for data retrieving, and a lot of passion & patience.

There was a couple of most difficult problems:

- Slow search. To overcome it, initially I wrote many SQL and (Python for SQL creation) to search faces inside DB itself. Then I made my SQL even more complex (in 2 stages), yet faster. It increased speed by another 30 times, so I spent avg 0.000004 sec to compare a face in DB. I wanted to make it parallel, but MySQL don't allow it. So, I thought about using multiple DBs or migrating to something more rapid, PostgreSQL or Paramiko.

- Slow Vk API and face recognition. To overcome this, I wrote multi-threading services that can work independently and send results to the server with DB. Then I rented a couple of servers (a pair of VPN and a real dedicated one), and asked my friends to generate access tokens. So, I had 3 servers with 2-10 running processes on each with 2-4 threads in each.

- And that led to the problem of multiple servers handling... To solve this I wrote Python scripts for quick and simple servers turning on/off, status checking over SSH. It is just awesome to get rid of console and control dozens of programs on remote servers with just a few clicks. And of course my central server had nice page with accumulated info about workers status, speed and DB size.

Eventually, I've got 25% of Vk users processed. But I thought that search by photo shouldn't be the only tool of my project, I created some code to find profiles by substring in their names, logins, or other linked accounts names (Instagram, Twitter, Facebook, Telegram). In addition, I made it possible to significantly reduce search time by filtering people by some groups or friends lists. I even wanted to create custom query language for mixing such lists (AND/OR logic).

But finally I understood that the project has no commercial prospects, and all of my exploratory interest was was completely satisfied. I started it somewhere in the October 2018, and closed in February 2019. I hope it may be interesting to other people.

![logo](http://aivanf.com/static/cv/ID-Liza-Simpson.png)

## License

 This software is provided 'as-is', without any express or implied warranty.
 You may not hold the author liable.

 Permission is granted to anyone to use this software for any purpose,
 including commercial applications, and to alter it and redistribute it freely,
 subject to the following restrictions:

 The origin of this software must not be misrepresented. You must not claim
 that you wrote the original software. When use the software, you must give
 appropriate credit, provide an active link to the original file, and indicate if changes were made.
 This notice may not be removed or altered from any source distribution.
