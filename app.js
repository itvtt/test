const express = require("express");
const path = require('path'); 
const app = express();
// const jwt = require("jsonwebtoken");
// const { Users } = require("./models");

// const loginRouter = require("./routes/signup");
// const postsRouter = require("./routes/posts");
// const commentsRouter = require("./routes/comments");
// const likeRouter = require("./routes/like");
// const router = express.Router();

// app.use(express.json());
app.use(express.static(path.join(__dirname, 'templates')));

app.get('/', (req, res) => {
  // res.send('Hello, World!');
  res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});


const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});


// // app.use([loginRouter,postsRouter,commentsRouter,likeRouter]);

// app.listen(8080, () => {
//   console.log("서버가 요청을 받을 준비가 됐어요");
//   console.log("gd")
// });