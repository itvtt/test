document.addEventListener("DOMContentLoaded", () => {
    const dropdownContainer = document.getElementById("dropdown-container");
    const contentSection = document.getElementById("dynamic-content");
    const searchBox = document.querySelector(".search-box input");
    const iframe = document.getElementById("dynamic-iframe");

    // 새로고침 여부 확인 및 처리
    const savedIframeSrc = localStorage.getItem("currentIframeSrc");
    const isReload = sessionStorage.getItem("isReload");

    if (isReload && savedIframeSrc) {
        // 새로고침 상태이며, 이전 페이지가 저장된 경우
        iframe.src = savedIframeSrc;
        iframe.style.display = "block";
    } else {
        // 처음 접속 상태: home.html로 초기화
        iframe.src = "/home";
        iframe.style.display = "block";
    }

    // 새로고침 여부 플래그 설정
    sessionStorage.setItem("isReload", "true");

    // iframe 높이 자동 조정 함수
    const adjustIframeHeight = () => {
        if (iframe.contentWindow) {
            const iframeDocument = iframe.contentWindow.document;
            if (iframeDocument && iframeDocument.body) {
                // 로드된 콘텐츠의 높이를 계산하고 iframe 높이에 반영
                const contentHeight = iframeDocument.body.scrollHeight+200;
                iframe.style.height = contentHeight + "px";
            }
        }
    };

    // iframe 내부 변경 감지 함수
    const observeIframeChanges = () => {
        if (iframe.contentWindow) {
            const iframeDocument = iframe.contentWindow.document;
            if (iframeDocument) {
                const observer = new MutationObserver(() => {
                    adjustIframeHeight(); // 콘텐츠 변경 시 높이 재조정
                });

                observer.observe(iframeDocument.body, {
                    childList: true, // 자식 요소 변화 감지
                    subtree: true,   // 하위 트리 변화 감지
                    attributes: true // 속성 변화 감지
                });
            }
        }
    };

    // iframe 로드 이벤트에서 높이 조정 및 변화 감지 시작
    iframe.addEventListener("load", () => {
        adjustIframeHeight();
        observeIframeChanges();

        // 현재 iframe src를 localStorage에 저장
        if (iframe.src && iframe.src !== "/home") {
            localStorage.setItem("currentIframeSrc", iframe.src);
        }
    });

    // 메뉴별 아이템 데이터
    const menuItems = {
        "MENU-MEETING": [
            { img: "https://via.placeholder.com/50", name: "AMAT 회의록", url: "/cal" },
            { img: "https://via.placeholder.com/50", name: "FRTP 회의록", url: "/home" },
        ],
        "MENU-MANAGE": [
            { img: "https://via.placeholder.com/50", name: "파츠 대여 관리", url: "/cal" },
            { img: "https://via.placeholder.com/50", name: "FOUP 관리", url: "/home" },
        ],
        "MENU-CENTURA": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", tag: "New" , url: "/cal"},
        ],
        "MENU-VANTAGE": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-FRTP": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-ESCALA": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-LSA": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-HPA": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-LOHAS": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-ARGOS": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-VIVA": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-SYSTEM": [
            { img: "https://via.placeholder.com/50", name: "ACS" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "BBS", url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "EES" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "DDIFE", url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "EFIJe" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "YMS", url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "IRS" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "DDS", url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "ILE" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        "MENU-ETC": [
            { img: "https://via.placeholder.com/50", name: "EFEM" , url: "/cal"},
            { img: "https://via.placeholder.com/50", name: "LL/TM", url: "/cal"},
        ],
        
    };

    // 드롭다운 렌더링 함수
    const renderDropdown = (menuId) => {
        dropdownContainer.innerHTML = ""; // 기존 내용 제거
        const items = menuItems[menuId];
        if (items) {
            items.forEach((item, index) => {
                const div = document.createElement("div");
                div.className = "item";
                div.setAttribute("data-url", item.url || "");
                div.innerHTML = `
                    <img src="${item.img}" alt="${item.name}">
                    <p>${item.name} ${item.tag ? `<span class="tag ${item.tag === "New" ? "new" : ""}">${item.tag}</span>` : ""}</p>
                `;
                dropdownContainer.appendChild(div);

                // 순차적 애니메이션 적용
                setTimeout(() => {
                    div.classList.add("visible");
                }, index * 10);

                // 클릭 이벤트 추가
                div.addEventListener("click", () => {
                    const url = div.getAttribute("data-url");
                    if (url) {
                        iframe.src = url; // 새로운 URL을 iframe에 로드
                        iframe.style.display = "block"; // iframe 표시
                        localStorage.setItem("currentIframeSrc", url); // 현재 iframe URL 저장
                    }
                    dropdownContainer.classList.remove("show"); 
                });
            });
            const closeButton = document.createElement("div");
            closeButton.className = "close-btn";
            closeButton.innerHTML = "X";
            dropdownContainer.appendChild(closeButton);

            // X 버튼 클릭 이벤트
            closeButton.addEventListener("click", () => {
                dropdownContainer.classList.remove("show"); // 드롭다운 닫기
            });
            dropdownContainer.classList.add("show");
        }
    };

    // 메뉴 클릭 이벤트
    document.querySelectorAll(".menu li").forEach((menuItem) => {
        menuItem.addEventListener("click", (e) => {
            const menuId = e.target.id;

            if (menuId === "MENU-HOME") {
                // Home 버튼 클릭 시 iframe 초기화
                iframe.src = "/home"; // Home 페이지 로드
                iframe.style.display = "block"; // iframe 표시
                localStorage.setItem("currentIframeSrc", "/home"); // Home URL 저장
                dropdownContainer.classList.remove("show"); // 드롭다운 닫기
                return;
            }
            if (menuId === "MENU-CALENDAR") {
                // Home 버튼 클릭 시 iframe 초기화
                iframe.src = "/cal"; // Home 페이지 로드
                iframe.style.display = "block"; // iframe 표시
                localStorage.setItem("currentIframeSrc", "/cal"); // Home URL 저장
                dropdownContainer.classList.remove("show"); // 드롭다운 닫기
                return;
            }

            // 드롭다운이 열려있고 동일 메뉴 클릭 시 닫음
            if (dropdownContainer.classList.contains("show") && dropdownContainer.dataset.menu === menuId) {
                dropdownContainer.classList.remove("show");
                return;
            }

            // 새 드롭다운 열기
            dropdownContainer.dataset.menu = menuId;
            renderDropdown(menuId);

            // iframe 유지 로직
            if (menuId !== "store-menu" && dropdownContainer.innerHTML === "") {
                // 다른 메뉴 클릭 시 드롭다운 항목이 없는 경우에도 iframe 유지
                iframe.style.display = "block";
            }
        });
    });

    // 드롭다운 외부 클릭 시 닫기
    document.addEventListener("click", (e) => {
        const menuClicked = [...document.querySelectorAll(".menu li")].some((menuItem) =>
            menuItem.contains(e.target)
        );
        if (!menuClicked && !dropdownContainer.contains(e.target)) {
            dropdownContainer.classList.remove("show");
        }
    });

    // 검색 기능
    document.querySelector(".search-box button").addEventListener("click", () => {
        const query = searchBox.value.trim();
        if (query) {
            // AJAX 요청을 통해 검색 결과 로드
            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then((response) => response.text())
                .then((html) => {
                    contentSection.innerHTML = html; // 검색 결과 표시
                })
                .catch((err) => {
                    console.error("검색 중 오류 발생:", err);
                    contentSection.innerHTML = "<p>검색 결과를 불러오는 중 오류가 발생했습니다.</p>";
                });
        }
    });
});
