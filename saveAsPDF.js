let btn = document.createElement('button');
btn.innerText = 'Download as PDF';
btn.setAttribute("id", "downloadButton")
btn.onclick = function(){window.print();};
document.body.appendChild(btn);
