var countDownFunc = function(endDAte){
  var second = 1000,
  minute = second * 60,
  hour = minute * 60,
  day = hour * 24;

var today = new Date(),
dd = String(today.getDate()).padStart(2, "0"),
mm = String(today.getMonth() + 1).padStart(2, "0"),
yyyy = today.getFullYear(),
nextYear = yyyy + 1,
dayMonth = endDAte,
voteday = dayMonth + yyyy;

today = mm + "/" + dd + "/" + yyyy;
if (today > voteday) {
voteday = dayMonth + nextYear;
}
//end

var countDown = new Date(voteday).getTime(),
x = setInterval(function() {    

  var now = new Date().getTime(),
        distance = countDown - now;

        var daychars = Math.floor(distance / (day));
        var dayArr = Array.from(daychars.toString()).map(Number);
        var dayres = dayArr.map(function(el, i) {
          return `<span>${el}</span>`;
        }).join('');

        var hourschars = Math.floor((distance % (day)) / (hour));
        var hoursArr = Array.from(hourschars.toString()).map(Number);
        var hoursres = hoursArr.map(function(el, i) {
          return `<span>${el}</span>`;
        }).join('');

        var minutechars = Math.floor((distance % (hour)) / (minute));
        var minuteArr = Array.from(minutechars.toString()).map(Number);
        var minuteres = minuteArr.map(function(el, i) {
          return `<span>${el}</span>`;
        }).join('');

        // var secondchars = Math.floor((distance % (minute)) / second);
        // var secondArr = Array.from(secondchars.toString()).map(Number);
        // var secondres = secondArr.map(function(el, i) {
        //   return `<span>${el}</span>`;
        // }).join('');

    document.getElementById("days").innerHTML = dayres,
    document.getElementById("hours").innerHTML = hoursres,
    document.getElementById("minutes").innerHTML = minuteres;
    // document.getElementById("seconds").innerHTML = secondres;

  //do something later when date is reached
  if (distance < 0) {
    document.getElementById("headline").innerText = "Voting Closed!";
    document.getElementById("countdown").style.display = "none";
    clearInterval(x);
  }
  //seconds
}, 0)
}


var voteDetailFunc = function(voted, nonVoted){
  var canvas = document.getElementById("electionchart");
  var ctx = canvas.getContext('2d');
  var gradientColors = [
  {
    start: '#CE2323',
    end: '#121567'
  },
  {
    start: '#F3F3F3',
    end: '#C8C8C8'
  }
  ];
  
  var gradients = [];
  
  gradientColors.forEach( function( item ){
      var gradient = ctx.createLinearGradient(150,0, 0,100);
      gradient.addColorStop(0, item.start);
      gradient.addColorStop(1, item.end);
      gradients.push(gradient);
  });
  
  
  var doughnutBar = new Chart(canvas, {
  
  type: 'doughnut',
  data: {
      labels: ["A", "B"],
      datasets: [{
          label: "Status",
          backgroundColor: gradients,
          borderColor: 'rgba(73, 79, 92, 0)',
          data: [voted, nonVoted]
      }]
  },
  options: {
      plugins: {
        aspectRatio: 1,
      cutoutPercentage: 90,
      responsive: true,
      startAngle: 0,
        legend: {
            display: false
        }
    }
  }
  });
  
}
