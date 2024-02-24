import RobotWindow from 'https://cyberbotics.com/wwi/R2023a/RobotWindow.js';

let historyHtml = "";

function receive (message){
	//Receive message from the python supervisor
	//Split on comma
	var parts = message.split(",");
	console.log(parts);

	//If there is a message
	if (parts.length > 0){			
		switch (parts[0]){
			case "startup":
				//Call for set up the robot window
				startup();
				break;
			case "update":
				//Update the information on the robot window every frame (of game time)
				update(parts.slice(1,parts.length + 1));
				break;
			case "config":
				//Load config data
				updateConfig(parts.slice(1,parts.length + 1));
				break;
			case "unloaded0":
				//Robot 0's controller has been unloaded
				unloadedController(0);
				break;
			case "unloaded1":
				//Robot 1's controller has been unloaded
				unloadedController(1);
				break;
			case "loaded0":
				//Robot 0's controller has been unloaded
				loadedController(0);
				break;
			case "loaded1":
				//Robot 1's controller has been unloaded
				loadedController(1);
				break;
			case "ended":
				//The game is over
				endGame();
				break;
			case "historyUpdate":
				let history0 = message.split(",").slice(1,message.length-1)
				updateHistory(history0)
				break;
			case "latest":
				document.getElementById("versionInfo").style.color = "#27ae60";
				document.getElementById("versionInfo").innerHTML = `Ver. ${parts[1]} (Latest)`;
				break;
			case "version":
				document.getElementById("versionInfo").innerHTML = `Ver. ${parts[1]}`;
				break;
			case "outdated":
				document.getElementById("versionInfo").style.color = "#c0392b";
				document.getElementById("versionInfo").innerHTML = `Ver. ${parts[1]} (Outdated)`;
				document.getElementById("newVersion").innerHTML = `New version: ${parts[2]} is available. Please update it!`;
				break;
			case "unreleased":
				document.getElementById("versionInfo").style.color = "#e67e22";
				document.getElementById("versionInfo").innerHTML = `Ver. ${parts[1]} (Unreleased)`;
				break;
				
			case "worlds":
				updateWorld(parts.slice(1));
				break;

			case "loadControllerPressed":
				window.openLoadController(parts[1]);
				break;
			case "unloadControllerPressed":
				window.unloadedController(parts[1]);
				break;
			case "runPressed":
				window.runPressed();
				break;
			case "runDockerPressed":
				window.runDockerPressed();
				break;
			case "pausedPressed":
				window.pausePressed();
				break;
			case "remoteEnabled":
				window.enableRemotePressed();
				break;
			case "remoteDisabled":
				window.disableRemotePressed();
				break;
			case "dockerSuccess":
				preRun();
				break;
			case "currentWorld":
				enableTestButton(parts[1]);
				break;
		}
	}
}

function updateWorld(worlds_str){
	//reset worlds
	document.getElementById("worlds_div").innerHTML = "";

	var worlds_array_str = String(worlds_str)
	let worlds = worlds_array_str.split(",");
	for (let i = 0; i < worlds.length; i ++){
		let button = document.createElement("button");
		button.innerHTML = worlds[i];
		button.onclick = function(){
			window.robotWindow.send(`loadWorld,${worlds[i]}`);
		};
		button.setAttribute("class","btn-world");

		// Add thumbnail to button
		let thumbnail = document.createElement("img");
		// Strip .wbt from name
		thumbnail.src = "./thumbnails/"+worlds[i].replace(/\.[^/.]+$/, "")+".png";
		thumbnail.height = 20;
		thumbnail.style = "vertical-align: middle;margin: 5px;";
		thumbnail.onerror = () => thumbnail.src = "./thumbnails/missing.png";
		button.appendChild(thumbnail)

		document.getElementById("worlds_div").appendChild(button);
		
	}
}


function updateHistory(history0){
	let html = "<tr>";
	if(history0[0].indexOf(":") != -1){
		if(history0[1].indexOf("+") != -1){
			html += `<td style='font-size:18px;color:#2980b9;width:'>${history0[0]}</td><td style='font-size:18px;color:#2980b9;'>${history0[1]}</td>`;
		}else if(history0[1].indexOf("-") != -1){
			html += `<td style='font-size:18px;color:#c0392b;'>${history0[0]}</td><td style='font-size:18px;color:#c0392b;'>${history0[1]}</td>`;
		}
		else if(history0[1].indexOf("WARNING") != -1) {
			html += `<td style='font-size:18px;color:#d98236;'>${history0[0]}</td><td style='font-size:18px;color:#d98236;'>${history0[1]}</td>`;
		}
		else{
			html += `<td style='font-size:18px;color:#2c3e50;'>${history0[0]}</td><td style='font-size:18px;color:#2c3e50;'>${history0[1]}</td>`;
		}
	}
	html += "</tr>";
	historyHtml = html + historyHtml;
	document.getElementById("history").innerHTML = historyHtml;
}

function resetHistory() {
	historyHtml = "";
	document.getElementById("history").innerHTML = "";
}

function loadedController(id){
	//A controller has been loaded into a robot id is 0 or 1 and name is the name of the robot
	//Set name and toggle to unload button for robot 0
	if (document.getElementById("keepRemote").checked && id == 0) return
	document.getElementById("load"+ id).style.display = "none";
	document.getElementById("unload"+ id).style.display = "inline-block";
	if (id == 0)
		disableWhileSending(false);
}

function unloadedController(id){
	//A controller has been unloaded for robot of the given id
	//Reset name and toggle to load button for robot 0
	document.getElementById("robot"+ id +"Controller").value = "";
	document.getElementById("unload"+ id).style.display = "none";
	document.getElementById("load"+ id).style.display = "inline-block";
}

function setEnableRemoteBtn() {
	document.getElementById("disableRemote").style.display = "none";
	document.getElementById("enableRemote").style.display = "inline-block";
}
function setDisableRemoteBtn() {
	document.getElementById("enableRemote").style.display = "none";
	document.getElementById("disableRemote").style.display = "inline-block";
}

function startup (){
	resetHistory();
	unloadedController(0);
	unloadedController(1);
	//Turn on the run button and reset button when the program has loaded
	setEnableButton("runButton", true);
	setEnableButton("runDockerButton", true);

	setEnableButton("pauseButton", false);
	setEnableButton('lopButton', false)

	setEnableButton("load0", true);
	setEnableButton("unload0", true);
	setEnableButton("load1", true);
	setEnableButton("unload1", true);
	setEnableButton("giveupB", false);

	setEnableButton("enableRemote", true);
	setEnableButton("disableRemote", true);
	setEnableButton("dockerPath", true);
	setEnableRemoteBtn();
	getWorlds();
}

window.getWorlds = function() {
	console.log("Getting worlds...")
	window.robotWindow.send('getWorlds');
}

function update (data){
	//Update the ui each frame of the simulation
	//Sets the the timer
	document.getElementById("score0").innerHTML = String(data[0]);

	//The total time at the start
	let maxTime = 8 * 60; 
	if (data[2]) { // is this necessary?
		maxTime = data[2]
	}
	maxTime = parseInt(maxTime);
	let maxRealTime = Math.max(maxTime + 60, maxTime * 1.25);
	document.getElementById("timer").innerHTML = calculateTimeRemaining(data[1], maxTime);
	document.getElementById("realWorldTimer").innerHTML = calculateTimeRemaining(data[3], maxRealTime);
}

function updateTestBtnState(state) {
	setEnableButton("test",!state);
}

function updateConfig (data){
	//Update the config ui
	document.getElementById("autoRemoveFiles").checked = Boolean(Number(data[0]));
	document.getElementById("autoLoP").checked = Boolean(Number(data[1]));
	document.getElementById("recording").checked = Boolean(Number(data[2]));
	document.getElementById("autoCam").checked = Boolean(Number(data[3]));
	if (data.length >= 5) {
		document.getElementById("keepRemote").checked = Boolean(Number(data[4]));
		if (Boolean(Number(data[4]))) window.enableRemotePressed()
		else window.disableRemotePressed()
		document.getElementById("enableDebugging").checked = Boolean(Number(data[5]))
		document.getElementById("dockerPath").value = String(data[6])
	}

	updateTestBtnState(Boolean(Number(data[0])))
}

window.configChanged = function(){
	let data = [0,0,0,0,0,0,""];
	data[0] = String(Number(document.getElementById("autoRemoveFiles").checked));
	data[1] = String(Number(document.getElementById("autoLoP").checked));
	data[2] = String(Number(document.getElementById("recording").checked));
	data[3] = String(Number(document.getElementById("autoCam").checked));
	data[4] = String(Number(document.getElementById("keepRemote").checked));
	data[5] = String(Number(document.getElementById("enableDebugging").checked))
	data[6] = String(document.getElementById("dockerPath").value)
	if (document.getElementById("keepRemote").checked) window.enableRemotePressed()
	else window.disableRemotePressed()

	updateTestBtnState(document.getElementById("autoRemoveFiles").checked)
	window.robotWindow.send(`config,${data.join(',')}`);
}

function calculateTimeRemaining(done, maxTime){
	//Create the string for the time remaining (mm:ss) given the amount of time elapsed
	//Convert to an integer
	done = Math.floor(done);
	//Calculate number of seconds remaining
	var remaining = maxTime - done;
	//Calculate seconds part of the time
	var seconds = Math.floor(remaining % 60);
	//Calculate the minutes part of the time
	var mins = Math.floor((remaining - seconds) / 60);
	//Convert parts to strings
	mins = String(mins)
	seconds = String(seconds)

	//Add leading 0s if necessary
	for (var i = 0; i < 2 - seconds.length; i++){
		seconds = "0" + seconds;
	}

	for (var i = 0; i < 2 - mins.length ; i++){
		mins = "0" + mins;
	}

	//Return the time string
	return mins + ":" + seconds;
}

function preRun() {
	//Disable all the loading buttons (cannot change loaded controllers once simulation starts)
	setEnableButton("load0", false);
	setEnableButton("unload0", false);
	
	setEnableButton("load1", false);
	setEnableButton("unload1", false);
	//When the run button is pressed
	//Disable the run button
	setEnableButton("runButton", false);
	setEnableButton("runDockerButton", false);
	//Send a run command
	//Enable the pause button
	setEnableButton("pauseButton", true);
	
	// setEnableButton('quit0', true)
	setEnableButton('lopButton', true)

	setEnableButton("giveupB", true);

	setEnableButton("enableRemote", false);
	setEnableButton("disableRemote", false);

	setEnableButton("dockerPath", false);
}

window.runPressed = function(){
	preRun();
	window.robotWindow.send("run");
}

window.runDockerPressed = function(){
	let docker_input = document.getElementById("dockerPath");
	window.robotWindow.send("runDocker,"+docker_input.value);
}

window.pausePressed = function(){
	//When the pause button is pressed
	//Turn off pause button, on run button and send signal to pause
	setEnableButton("pauseButton", false);
	setEnableButton("runButton", true);
	setEnableButton('lopButton', false)
	window.robotWindow.send("pause");
}

window.resetPressed = function(){
	//When the reset button is pressed
	//Disable all buttons
	setEnableButton("runButton", false);
	setEnableButton("pauseButton", false);
	setEnableButton('lopButton', false);
	//Send signal to reset everything
	window.robotWindow.send("reset");
}

window.testPressed = function() {
	preRun();
	window.robotWindow.send("loadTest");
	window.robotWindow.send("runTest");
}

window.giveupPressed = function(){
	if(document.getElementById("giveupB").className == "btn-giveup"){
		window.robotWindow.send("quit,0");
		setEnableButton("runButton", false)
		setEnableButton("pauseButton", false);
		setEnableButton('lopButton', false)
		setEnableButton('giveupB', false)
	}
}

window.openLoadController = function(id){
	//When a load button is pressed - opens the file explorer window
	document.getElementById("robot"+id+"Controller").click();
	window.robotWindow.send("loadControllerPressed,"+id);
}

function setEnableButton(name, state){
	//Set the disabled state of a button (state is if it is enabled as a boolean)
	document.getElementById(name).disabled = !state;
	if(name == "giveupB"){
		if(state) document.getElementById(name).className = "btn-giveup"
		else document.getElementById(name).className = "btn-giveupD"
	}
}

//Set the onload command for the window
window.onload = function(){
	//Connect the window
	window.robotWindow = new RobotWindow();
	//Set the title
	window.robotWindow.setTitle('Erebus Simulation Controls');
	//Set which function handles the recieved messages
	window.robotWindow.receive = receive;
	//Set timer to inital time value
	document.getElementById("timer").innerHTML = 'Initializing'
	window.robotWindow.send("rw_reload");
};

function endGame(){
	//Once the game is over turn off both the run and pause buttons
	setEnableButton("runButton", false)
	setEnableButton("pauseButton", false);
	setEnableButton('lopButton', false)
}

window.unloadPressed = function(id){
	//Unload button pressed
	//Send the signal for an unload for the correct robot
	window.robotWindow.send("robot"+id+"Unload");
	window.robotWindow.send("unloadControllerPressed,"+id);
}

function disableWhileSending(disabled) {
	setEnableButton("load0", !disabled);
	setEnableButton("unload0", !disabled);
	
	setEnableButton("load1", !disabled);
	setEnableButton("unload1", !disabled);
	
	setEnableButton("runButton", !disabled);
}


window.fileOpened = function(filesId, acceptTypes, location, id){
	//When file 0 value is changed
	//Get the files
	var files = document.getElementById(filesId).files;

	//If there are files
	if (files.length > 0){
		//Get the first file only
		var file = files[0];
		//Split at the .
		var nameParts = file.name.split(".");

		//If there are parts to the name
		if (nameParts.length >= 1){
			//If the file extension is valid
			if(nameParts.length == 1 || acceptTypes.indexOf(nameParts[nameParts.length - 1]) != -1 ){
				const fd = new FormData();
				for (let i = 0; i < files.length; i++) {
					const f = files[i];
					fd.append(`file${(i+1)}`, f, f.name);
				}

				let xmlhttp = new XMLHttpRequest();
				xmlhttp.onreadystatechange = function () {
					if (xmlhttp.readyState == 4 && xmlhttp.status != 200) {
						console.log(xmlhttp.status);
						alert(xmlhttp.responseText);
					}
					if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
						loadedController(id);
					}
				};
				disableWhileSending(true);
				xmlhttp.open("POST", "http://127.0.0.1:60520/"+location+"/", true);
				xmlhttp.send(fd);
			}else{
				//Tell the user to select a program
				alert("Please select a controller with a valid file type from: .py, .exe, .class, .jar, .bsg, .m or no extension (for Linux/Mac users)");
			}
		}else{
			//Tell the user to select a program
			alert("Please select a controller program");
		}

	}
}

window.openJsonFile = function(){
	//When file 0 value is changed
	//Get the files
	var files = document.getElementById("robot1Controller").files;
	
	//If there are files
	if (files.length > 0){
		//Get the first file only
		var file = files.item(0);
		//Split at the .
		var nameParts = file.name.split(".");
		
		//If there are parts to the name
		if (nameParts.length > 1){
			//If the last part is "json" - a json file
			if(nameParts[nameParts.length - 1] == "json"){
				//Create a file reader
				var reader = new FileReader();
				
				//Set the function of the reader when it finishes loading
				reader.onload = (function(reader){
					return function(){
						//Send the signal to the supervisor with the data from the file
						window.robotWindow.send("robotJson," + reader.result);
					}
				})(reader);
				
				//Read the file as udf-8 text
				reader.readAsText(file);
			}else{
				//Tell the user to select a json file
				alert("Please select a json file.");
			}
		}else{
			//Tell the user to select a json file
			alert("Please select a json file.");
		}
		
	}
}

window.relocate = function(id){
	window.robotWindow.send("relocate,"+id.toString());
}

window.quit = function(id){
	unloadPressed(id);
	window.robotWindow.send("quit,"+id.toString());
}

window.enableRemotePressed = function() {
	setEnableButton("load0", false);
	setEnableButton("unload0", false);
	setDisableRemoteBtn();
	window.robotWindow.send("remoteEnable");
}
window.disableRemotePressed = function() {
	setEnableButton("load0", true);
	setEnableButton("unload0", true);
	setEnableRemoteBtn();
	let keep_before = document.getElementById("keepRemote").checked
	document.getElementById("keepRemote").checked = false
	if (keep_before) configChanged()
	window.robotWindow.send("remoteDisable");
}

function enableTestButton(world_name) {
	if (world_name != ".Tests"){ 
		document.getElementById("dev-tests").style.display = "none";
		return;
	}
	document.getElementById("dev-tests").style.display = "block";
}