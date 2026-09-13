# Wake Word Setup

The financial skill does not detect the wake word itself. RaspOVOS/OVOS listens for the wake word, removes it from the utterance, and sends the remaining command to this skill.

Use this interaction:

```text
Hey Mycroft
What is my balance?
```

The wake word is `Hey Mycroft`. The command is matched by `BalanceIntent.voc`.

## Configure RaspOVOS

On the Raspberry Pi, install and enable one OVOS wake-word plugin supported by your RaspOVOS image. For example, use the wake-word plugin already included by the image and select `hey_mycroft` as the active hotword.

In the OVOS configuration, the relevant settings should be equivalent to:

```json
{
  "listener": {
    "wake_word": "hey_mycroft"
  }
}
```

The exact configuration file and plugin name depend on the RaspOVOS image. Do not add `Hey Mycroft` to `BalanceIntent.voc` or `SpendingIntent.voc`; OVOS should remove the activation word before intent matching.

## Verify the listener

Restart the OVOS services after changing the listener configuration. Then test in this order:

1. Say `Hey Mycroft` and wait for the listening indicator.
2. Say `What is my balance?`.
3. Say `How much did I spend?`.

If the wake word is not detected, test the wake-word plugin before testing this skill. If the wake word works but the command does not, test the skill vocabulary and intent registration.

## Firefly connection

The Raspberry Pi must use the PC's LAN address, not `localhost` and not the Docker service name `app`:

```env
FIREFLY_III_URL=http://192.168.137.1/api/v1
FIREFLY_III_ACCESS_TOKEN=your_firefly_token
```

Replace `192.168.137.1` with the actual address of the computer running Firefly III.
