# React Ref Timing: Async State + Conditional Rendering

## The Bug

```jsx
function Component() {
  const [player, setPlayer] = useState(null);
  const audioRef = useRef(null);

  const loadTrack = async () => {
    const data = await fetchTrack();
    setPlayer(data);                    // schedules re-render
    const a = audioRef.current;         // ❌ null — DOM hasn't updated yet!
    if (a) {
      a.src = data.streamUrl;           // never executes
      a.play();
    }
  };

  return (
    <div>
      {!player ? (
        <EmptyState />
      ) : (
        <audio ref={audioRef} controls />   // not rendered yet
      )}
    </div>
  );
}
```

**Root cause:** `setPlayer(data)` is a state update — React batches it and schedules a re-render. The code after `setPlayer()` still runs in the **current render**, where `player` was null, so `<audio>` wasn't in the DOM and `audioRef.current` is `null`.

## The Fix: useEffect to react to state change

```jsx
function Component() {
  const [player, setPlayer] = useState(null);
  const audioRef = useRef(null);

  const loadTrack = async () => {
    const data = await fetchTrack();
    setPlayer(data);     // triggers re-render, audio element mounts
  };

  // Runs AFTER the re-render — audio element exists in DOM
  useEffect(() => {
    if (!player) return;
    const a = audioRef.current;
    if (a) {
      a.src = player.streamUrl;
      a.play();
    }
  }, [player]);

  return (
    <div>
      {!player ? (
        <EmptyState />
      ) : (
        <audio ref={audioRef} controls />   // rendered ✓
      )}
    </div>
  );
}
```

## Bonus: Race Condition Protection

When the user can trigger `loadTrack()` rapidly, stale async responses can overwrite newer state:

```jsx
const reqIdRef = useRef(0);

const loadTrack = async () => {
  const thisReq = ++reqIdRef.current;
  setLoading(true);
  const data = await fetchTrack();
  if (thisReq !== reqIdRef.current) return;  // stale — discard
  setPlayer(data);
};
```

## Related Patterns

- Same issue applies to ANY DOM API call right after `setState()` with conditional rendering: `ref.current.focus()`, `ref.current.scrollIntoView()`, `ref.current.getBoundingClientRect()`.
- Works both ways: if setting state in an event handler or async callback, the ref isn't available until the next React commit.
