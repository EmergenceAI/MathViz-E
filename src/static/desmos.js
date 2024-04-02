const elt = document.getElementById('calculator');
const calculator = Desmos.GraphingCalculator(elt);
const serviceURL = window.origin;
console.log("Service URL : "+serviceURL);

function updateExpressions(expressions) {
    try {
        for (let i = 0; i < expressions.length; i++) {
            if (expressions[i]["action"] == "setExpression") {
                var exp = expressions[i]["expression"]
                calculator.setExpression(exp)
            }
            else if (expressions[i]["action"] == "removeExpression") {
                var exp = expressions[i]["expression"]
                calculator.removeExpression(exp);
            }
        }
    }
    catch (exp) {
        console.error(exp);
    }
}

function getExpressions() {
    const inputExpressions = calculator.getExpressions().map(expr=>JSON.stringify(expr));
    return inputExpressions
}

function interpretUtterance(sessionid, message, expressions) {
    fetch(serviceURL+"/desmos/interpret", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionid: sessionid,
            text: message,
            expressions: expressions,
        })
    })
        .then(response => {
            console.log(response);
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            reader.read().then(function processText({ done, value }) {
                if (done) {
                    console.log('Stream complete');
                    console.log(value);
                    return;
                }
                buffer += decoder.decode(value);
                const parts = buffer.split('\n');
                buffer = parts.pop();
                for (const part of parts) {
                    try {
                        console.log("Parts : "+part);
                        console.log(part);
                        let response = JSON.parse(part);
                        
                        if ("expressions" in response) {
                            let expression = response["expressions"];
                            updateExpressions(expression);
                        }
                        else if ("agent" in response) {
                            updateExplanationPanel(response["agent"], response["message"]);
                        }
                    }
                    catch (error) {
                        console.error(error);
                       
                    }
                }
                return reader.read().then(processText);
            });
        })
        .catch(error => {
            console.error(error);
           
        });
}

function clearBackend(sessionid){
    console.log("Clearing backend");
    fetch(serviceURL+"/desmos/clear", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionid: sessionid
        })
    })
        .then(response => {
            console.log(response);
        })
        .catch(error => {
            console.error(error);
        });
}

function clearDesmos() {
    calculator.setBlank();
}
