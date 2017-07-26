let btn = document.createElement('button');
btn.innerText = 'Download as PDF';
btn.onclick = function(){window.print();};
document.body.appendChild(btn);
