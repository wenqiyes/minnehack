function getCookie(cname) {let name = cname + "=";let decodedCookie = decodeURIComponent(document.cookie);let ca = decodedCookie.split(';');for(let i = 0; i <ca.length; i++) {let c = ca[i];while (c.charAt(0) == ' ') {c = c.substring(1);}if (c.indexOf(name) == 0) {return c.substring(name.length, c.length);}return "";}
            fetch("https://backend.minnehackteam.repl.co/verifyToken?token="+getCookie("token")).then(x => x.text()).then(function(y){ if (y=="true"){
              let classs = document.getElementsByClassName("loginout");
              for(let i = 0; i<classs.length; i++) {
                classs[i].classList.toggle("hidden");
              }
            }})