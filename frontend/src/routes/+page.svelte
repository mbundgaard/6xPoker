<script>
	let apiStatus = $state('Checking...');
	let wsStatus = $state('Disconnected');
	let wsMessage = $state('');
	let inputMessage = $state('');
	let ws = $state(null);

	async function checkApi() {
		try {
			const response = await fetch('/api/health');
			const data = await response.json();
			apiStatus = `${data.status}: ${data.message}`;
		} catch (error) {
			apiStatus = `Error: ${error.message}`;
		}
	}

	function connectWebSocket() {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

		ws.onopen = () => {
			wsStatus = 'Connected';
		};

		ws.onmessage = (event) => {
			wsMessage = event.data;
		};

		ws.onclose = () => {
			wsStatus = 'Disconnected';
			ws = null;
		};

		ws.onerror = (error) => {
			wsStatus = 'Error';
		};
	}

	function sendMessage() {
		if (ws && inputMessage) {
			ws.send(JSON.stringify({ text: inputMessage }));
			inputMessage = '';
		}
	}

	$effect(() => {
		checkApi();
	});
</script>

<main style="padding: 2rem; font-family: sans-serif;">
	<h1>6x Poker</h1>

	<section style="margin: 2rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px;">
		<h2>API Health Check</h2>
		<p>Status: <strong>{apiStatus}</strong></p>
		<button onclick={checkApi}>Refresh</button>
	</section>

	<section style="margin: 2rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px;">
		<h2>WebSocket Test</h2>
		<p>Status: <strong>{wsStatus}</strong></p>

		{#if !ws}
			<button onclick={connectWebSocket}>Connect</button>
		{:else}
			<div style="margin: 1rem 0;">
				<input
					type="text"
					bind:value={inputMessage}
					placeholder="Type a message..."
					onkeypress={(e) => e.key === 'Enter' && sendMessage()}
				/>
				<button onclick={sendMessage}>Send</button>
			</div>
		{/if}

		{#if wsMessage}
			<p>Server response: <code>{wsMessage}</code></p>
		{/if}
	</section>
</main>
