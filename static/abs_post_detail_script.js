

// 댓글 추가
function addComment(event) {
    event.preventDefault();
    const author = document.getElementById("new-author").value.trim();
    const comment = document.getElementById("new-comment").value.trim();

    if ( !comment) {
        alert(" 댓글 내용을 입력해주세요.");
        return;
    }

    commentCount++;
    const newComment = `
        <div class="comment-item" id="comment-${commentCount}">
            <div class="comment-content">
                <p><strong>${author}</strong></p>
                <p>${comment}</p>
                <small>${new Date().toLocaleString()}</small>
            </div>
            <div class="comment-actions">
                <button class="action-menu" onclick="toggleActions(${commentCount})">...</button>
                <div id="actions-${commentCount}" class="actions-menu" style="display: none;">
                    <button class="comment-edit-button" onclick="showEditForm(${commentCount})">수정</button>
                    <button class="comment-delete-button" onclick="deleteComment(${commentCount})">삭제</button>
                </div>
            </div>
        </div>

        <div id="edit-form-${commentCount}" class="comment-edit" style="display: none;">
            <textarea placeholder="댓글 내용">${comment}</textarea>
            <div class="edit-actions">
                <button class="cancel-button" onclick="hideEditForm(${commentCount})">취소</button>
                <button class="save-button">등록</button>
            </div>
        </div>
    `;

    const commentsSection = document.querySelector(".comments-section");
    commentsSection.insertAdjacentHTML("beforeend", newComment);

    document.getElementById("new-author").value = "";
    document.getElementById("new-comment").value = "";
    }
    // 댓글 입력창에서 클립보드 이미지를 Base64로 변환하고 미리보기로 표시
    document.getElementById("comment-editor").addEventListener("paste", function (event) {
        const clipboardData = event.clipboardData || window.clipboardData;
        const items = clipboardData.items;

        for (const item of items) {
            if (item.type.indexOf("image") !== -1) {
                const file = item.getAsFile();
                const reader = new FileReader();

                reader.onload = function (event) {
                    const base64Image = event.target.result;

                    // Base64 이미지를 댓글 본문에 추가
                    const commentEditor = document.getElementById("comment-editor");
                    const imgElement = document.createElement("img");
                    imgElement.src = base64Image;
                    imgElement.style.maxWidth = "200px";
                    imgElement.style.maxHeight = "200px";
                    imgElement.style.marginTop = "10px";
                    commentEditor.appendChild(imgElement);
                };

                reader.readAsDataURL(file); // 이미지 파일을 Base64로 변환
                event.preventDefault(); // 기본 붙여넣기 동작 방지
                return;
            }
        }
    });
    document.getElementById("comment-form").addEventListener("submit", function (event) {
    const editorContent = document.getElementById("comment-editor").innerHTML; // Get content from editor
    const commentTextarea = document.getElementById("comment-textarea");
    const authorInput = document.getElementById("author-input");

    // Check if the content or author is empty
    if (!editorContent.trim()) {
        alert("댓글 내용을 입력해주세요.");
        event.preventDefault(); // Stop form submission
        return;
    }

    // Populate hidden textarea with content
    commentTextarea.value = editorContent;

    console.log("Form data ready for submission:", {
        author: authorInput.value,
        comment: commentTextarea.value,
    });
});

const commenteditbutton = document.getElementById("modifybtn");
const commenteditbutton2 = document.getElementById("modifybtn2");
function showEditForm(commentId) {
    const commentText = document.getElementById(`comment-text-${commentId}`);
    const editForm = document.getElementById(`edit-form-${commentId}`);

    if (!commentText || !editForm) {
        console.error(`Elements not found for commentId: ${commentId}`);
        return;
    }

    // 기존 텍스트 숨기고 수정 폼 표시
    commentText.style.display = "none";
    editForm.style.display = "block";
    commenteditbutton.style.display = "none";
    commenteditbutton2.style.display = "none";
}

function cancelEditForm(commentId) {
    const commentText = document.getElementById(`comment-text-${commentId}`);
    const editForm = document.getElementById(`edit-form-${commentId}`);

    if (!commentText || !editForm) {
        console.error(`Elements not found for commentId: ${commentId}`);
        return;
    }

    // 수정 폼 숨기고 기존 텍스트 표시
    editForm.style.display = "none";
    commentText.style.display = "block";
}


function cancelEdit(commentId) {
    // 수정 창 숨기기 및 기존 댓글 내용 표시
    const commentText = document.getElementById(`comment-text-${commentId}`);
    const editForm = document.getElementById(`edit-form-${commentId}`);
    editForm.style.display = "none";
    commentText.style.display = "block";
}

function saveEdit(commentId) {
    const textarea = document.getElementById(`edit-textarea-${commentId}`);
    const updatedComment = textarea.value.trim();

    if (!updatedComment) {
        alert("수정 내용을 입력해주세요.");
        return;
    }

    // 서버에 수정 요청 보내기
    fetch(`/post/${post['id']}/comment/${commentId}/edit`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ comment: updatedComment }),
    })
    .then((response) => {
        if (response.ok) {
            // 성공적으로 수정되었을 경우 UI 업데이트
            const commentText = document.getElementById(`comment-text-${commentId}`);
            commentText.innerText = updatedComment;
            cancelEdit(commentId); // 수정 창 닫기
        } else {
            alert("댓글 수정에 실패했습니다.");
        }
    })
    .catch((error) => {
        console.error("Error:", error);
        alert("댓글 수정 중 오류가 발생했습니다.");
    });
}

// 대댓글부분
function showReplyForm(commentId) {
  // 해당 댓글의 대댓글 입력 폼을 토글
  const replyForm = document.getElementById(`reply-form-${commentId}`);
  if (replyForm) {
    replyForm.style.display = replyForm.style.display === "none" ? "block" : "none";
  } else {
    console.error(`Reply form with ID reply-form-${commentId} not found.`);
  }
}


function submitReply(commentId) {
  const replyForm = document.getElementById(`reply-form-${commentId}`);
  const textarea = replyForm.querySelector("textarea");

  if (!textarea.value.trim()) {
    alert("대댓글 내용을 입력해주세요.");
    return;
  }

  const replyData = {
    reply: textarea.value.trim(),
  };

  console.log("Submitting reply data:", replyData); // 디버깅용 출력

  fetch(`/post/97/comment/${commentId}/reply`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(replyData),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => {
          console.error("Error response from server:", data);
          alert(data.error || "대댓글 작성 중 오류가 발생했습니다.");
        });
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server response:", data);
      location.reload(); // 새로고침하여 변경 사항 반영
    })
    .catch((error) => {
      console.error("Fetch error:", error);
      alert("서버와 통신 중 오류가 발생했습니다.");
    });
}


// 대댓글ㄹ르

function editReply(replyId) {
  const replyTextElement = document.getElementById(`reply-text-${replyId}`);

  // 요소 존재 여부 확인
  if (!replyTextElement) {
    console.error(`Element with ID reply-text-${replyId} not found.`);
    return;
  }

  const originalText = replyTextElement.innerText;

  // 수정 폼 생성
  const editForm = document.createElement("div");
  editForm.innerHTML = `
    <textarea>${originalText}</textarea>
    <button onclick="saveReply(${replyId})">저장</button>
    <button onclick="cancelEditReply(${replyId}, '${originalText}')">취소</button>
  `;

  // 기존 내용을 수정 폼으로 대체
  replyTextElement.parentElement.replaceChild(editForm, replyTextElement);
}
function cancelEditReply(replyId, originalText) {
  const replyElement = document.getElementById(`reply-${replyId}`);
  const replyContent = `
    <p id="reply-text-${replyId}">${originalText}</p>
  `;
  replyElement.querySelector(".reply-content").innerHTML = replyContent;
}


// 대댓글 수정 저장
function saveReply(replyId) {
  const replyElement = document.getElementById(`reply-${replyId}`);
  const textarea = replyElement.querySelector("textarea");

  if (!textarea) {
    console.error(`Textarea for reply ID ${replyId} not found.`);
    return;
  }

  const updatedText = textarea.value.trim();

  // 서버에 저장 요청
  fetch(`/reply/${replyId}/edit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reply: updatedText }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to update reply");
      }
      return response.json();
    })
    .then((data) => {
      // DOM 업데이트
      const replyContent = `
        <p id="reply-text-${replyId}">${updatedText}</p>
        <small>${data.updated_at}</small>
      `;
      const contentContainer = replyElement.querySelector(".reply-content");
      if (contentContainer) {
        contentContainer.innerHTML = replyContent;
        
      } else {
        console.error(`Reply content container for ID ${replyId} not found.`);
        
      }
      location.reload(); // 새로고침하여 변경 사항 반영
    })
    .catch((error) => {
      alert("대댓글 수정에 실패했습니다.");
      console.error(error);
    });
}


// 수정 취소
function cancelEditReply(replyId, originalText) {
  const replyElement = document.getElementById(`reply-${replyId}`);
  replyElement.querySelector(".reply-content").innerHTML = `
    <p id="reply-text-${replyId}">${originalText}</p>
  `;
}

// 대댓글 삭제
function deleteReply(replyId) {
  if (!confirm("정말 삭제하시겠습니까?")) return;

  fetch(`/reply/${replyId}/delete`, { method: "DELETE" })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to delete reply");
      }
      document.getElementById(`reply-${replyId}`).remove();
    })
    .catch((error) => {
      alert("대댓글 삭제에 실패했습니다.");
      console.error(error);
    });
}
function copyToClipboard() {
          const currentUrl = window.location.href; // 현재 URL 가져오기
          navigator.clipboard
            .writeText(currentUrl)
            .then(() => {
              alert("링크가 복사되었습니다!"); // 성공 메시지
            })
            .catch(err => {
              console.error("링크 복사에 실패했습니다: ", err);
            });
        }
        function copyToClipboard2() {
          const currentUrl = window.location.href; // 현재 URL 가져오기
          const embedCode = `<iframe src="${currentUrl}" width="600" height="400" frameborder="0" allowfullscreen></iframe>`; // HTML 임베드 코드 생성
          navigator.clipboard
            .writeText(embedCode)
            .then(() => {
              alert("임베드 코드가 복사되었습니다!"); // 성공 메시지
            })
            .catch(err => {
              console.error("임베드 코드 복사에 실패했습니다: ", err);
            });
        }
        function toggleMenu() {
    const menu = document.getElementById("menu");
    if (menu.classList.contains("menu-hidden")) {
      menu.classList.remove("menu-hidden");
      menu.classList.add("menu-visible");
    } else {
      menu.classList.remove("menu-visible");
      menu.classList.add("menu-hidden");
    }
  }

  function confirmDelete() {
    return confirm("정말 삭제하시겠습니까?");
  }
