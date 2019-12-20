document.getElementById("playAgain").style.display="none";

var path = 'data/Quiz'

// Define Dance Names
var walzer = new Array();
walzer[0] = "D978walzer01.mp3";
walzer[1] = "D980walzer01.mp3";
walzer[2] = "D980walzer02.mp3"; 
walzer[3] = "D365walzer07.mp3";
walzer[4] = "D365walzer21.mp3";
walzer[5] = "D145walzer10.mp3";
walzer[6] = "D145walzer09.mp3";
walzer[7] = "D145walzer08.mp3";

var menuette = new Array();
menuette[0] = "D041menuett02a.mp3";
menuette[1] = "D041menuett11a.mp3";
menuette[2] = "D334menuett01a.mp3";
menuette[3] = "D041menuett18a.mp3";
menuette[4] = "D041menuett19a.mp3";
menuette[5] = "D041menuett20a.mp3";
menuette[6] = "D041menuett17a.mp3";
menuette[7] = "D041menuett16a.mp3";


var trios = new Array();
trios[0] = "D041trio07b.mp3";
trios[1] = "D041trio16b.mp3";
trios[2] = "D146trio04b.mp3";
trios[3] = "D146trio07b.mp3";
trios[4] = "D146trio20b.mp3";
trios[5] = "D041trio14b.mp3";
trios[6] = "D041trio15b.mp3";
trios[7] = "D041trio13b.mp3";

var laendler = new Array();
laendler[0] = "D366ländler05.mp3";
laendler[1] = "D366ländler08.mp3";
laendler[2] = "D366ländler12.mp3";
laendler[3] = "D378ländler01.mp3";
laendler[4] = "D378ländler08.mp3";
laendler[5] = "D145ländler15.mp3";
laendler[6] = "D145ländler16.mp3";
laendler[7] = "D145ländler17.mp3";;

var deutsche = new Array();
deutsche[0] = "D420deutscher04.mp3";
deutsche[1] = "D783deutscher04.mp3";
deutsche[2] = "D783deutscher13.mp3";
deutsche[3] = "D972deutscher02.mp3";
deutsche[4] = "D972deutscher03.mp3";
deutsche[5] = "D128deutscher10.mp3";
deutsche[6] = "D128deutscher11.mp3";
deutsche[7] = "D128deutscher12.mp3";

var ecossaise = new Array();
ecossaise[0] = "D697ecossaise02.mp3";
ecossaise[1] = "D697ecossaise04.mp3";
ecossaise[2] = "D781ecossaise03.mp3";
ecossaise[3] = "D781ecossaise04.mp3";
ecossaise[4] = "D781ecossaise05.mp3";
ecossaise[5] = "D735ecossaise04.mp3";
ecossaise[6] = "D735ecossaise05.mp3";
ecossaise[7] = "D735ecossaise06.mp3";

function getRandom(danceArray) {
    var randDance = danceArray[Math.floor(Math.random()*danceArray.length)]
    return randDance
}

function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }
  alert(String(array))
  return array;
}

randWalzer = getRandom(walzer);
randMenuett = getRandom(menuette);
randTrio = getRandom(trios);
randLaendler = getRandom(laendler);
randEcossaise = getRandom(ecossaise);

randDances = new Array();
randDances[0] = randWalzer;
randDances[1] = randMenuett;
randDances[2] = randTrio;
randDances[3] = randLaendler;
randDances[4] = randEcossaise;

randDances = shuffle(randDances)

var maxRounds = 5;
var roundCount = 1;
var rightAnswers = 0;
var selectedAnswer = false;

var audioElement=document.getElementById('dance');
audioElement.src= path + '/' + randDances[roundCount-1] + '';

function reset() {
	randWalzer = getRandom(walzer);
	randMenuett = getRandom(menuette);
	randTrio = getRandom(trios);
	randLaendler = getRandom(laendler);
	randEcossaise = getRandom(ecossaise);
	
	randDances = new Array();
	randDances[0] = randWalzer;
	randDances[1] = randMenuett;
	randDances[2] = randTrio;
	randDances[3] = randLaendler;
	randDances[4] = randEcossaise;
	
	randDances = shuffle(randDances)
	
	var maxRounds = 5;
	var roundCount = 1;
	var rightAnswers = 0;
	var selectedAnswer = false;
	
	document.getElementById("answer").textContent = " "; 
	document.getElementById('nextRound').textContent = "Next round"
	document.getElementById('nextRound').style.display = "block"
	document.getElementById("playAgain").style.display="none";
	document.getElementById("round").textContent = "Round "+String(roundCount)+"/"+String(maxRounds);
	
	var audioElement=document.getElementById('dance');
	audioElement.src= path + '/' + randDances[roundCount-1] + '';
}

function dancePlay(){
    audioElement.play();
}
    
function dancePause(){
    audioElement.pause();
} 
    
function select(){
	if (selectedAnswer == false) {
		var e = document.getElementById("dropdown");
		var value = e.options[e.selectedIndex].value;
		
		if (value == 'default') {
			document.getElementById("answer").textContent="Please select an answer from the dropdown.";
		}
		else {
			if (randDances[roundCount-1].includes(value)){
				document.getElementById("answer").textContent="Right answer";
				rightAnswers++;
			}
			else {
				var trueAnswer=  randDances[roundCount-1].match(/[a-zA-Z-ä]+/g)[1];
				trueAnswer = trueAnswer[0].toUpperCase() + trueAnswer.slice(1); 
				document.getElementById("answer").textContent="Wrong answer. This was a " + String(trueAnswer) + ".";         
			}
			selectedAnswer = true;
		}
	}
	else {
		document.getElementById("answer").textContent="Answer already given, proceed to next round.";
	}
}

function nextRound() {
	if (selectedAnswer==false) {
		document.getElementById("answer").textContent="Please select an answer.";
	}
	else {
		if (roundCount < maxRounds) {
			roundCount++
			var audioElement=document.getElementById('dance');
			audioElement.src= path + '/' + randDances[roundCount-1] + '';
			
			document.getElementById("answer").textContent="\n";
			
			if (roundCount==maxRounds) {
				document.getElementById('nextRound').textContent = "Finish"
			}
			document.getElementById("round").textContent = "Round "+String(roundCount)+"/"+String(maxRounds);			
		}
		else {
			document.getElementById("answer").textContent = "Quiz finished! You got "+rightAnswers+" answers right."; 
			document.getElementById("nextRound").style.display="none";
			document.getElementById("playAgain").style.display="block";
		}
		document.getElementById("dropdown").options[0].selected = true;
		selectedAnswer = false;
	}
}
