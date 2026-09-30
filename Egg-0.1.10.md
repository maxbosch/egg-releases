# Egg 0.1.10

First run walks you through the iMessage setup instead of describing it, the
shelf's sandbox starts before you need it, and Egg Mode stops swallowing the
click on a plain desktop.

- **The setup is a flow now, not a paragraph.** Giving Egg its own address
  means a web flow behind Apple ID auth, an emailed six-digit code and a
  checkbox in Messages — three apps and six steps, which both places that
  asked for the address had compressed into one sentence above a text field.
  First launch now walks it: grants, then the address, then a test message
  that proves both. It suggests an address derived from your own, copies it,
  opens appleid.apple.com and then Messages, and waits to see something land
  before calling the setup done. Fourteen states, and nothing is written
  until the flow finishes — abandoning it halfway leaves your configuration
  exactly as it was.
- **You can get back to it.** The walkthrough used to be reachable only on
  first launch and from a Welcome item buried in the app menu, so anyone who
  dismissed it — or upgraded into it — could not return. Settings has **Set
  Up Egg's Address…** beside the field (**Change Address…** once set), and
  the checklist row grows a **Set Up Address…** button while no address
  exists. The field stays for anyone who already has an address.
- **Allow Contacts asks, rather than naming a switch that isn't there.**
  The Messages panel sent testers to System Settings › Privacy & Security ›
  Contacts to find an empty list: macOS lists an app there only after it has
  asked, and Egg hadn't. Not-asked is now resolved by asking — a button
  fires the real prompt and re-reads the panel, so the same line answers
  whether it worked. The System Settings path stays for denied, where it is
  the only route left.
- **The shelf's VM is warm before the first send.** The Active band opens
  with a Shelf sandbox row, labelled Cloud VM or Local VM, and **Start**
  boots it up front so a send doesn't wait out 20–60 seconds of boot. The
  row shows booting with a timer, then ready with driver, uptime and time
  left. Start, Send and the instant actions now share one in-flight boot
  instead of each booting a VM and leaving the extras to idle out, every
  reuse renews the lease, and reconnecting to a prototype renews its hour so
  it can't be reaped mid-edit.
- **The sandbox runs on Firecracker.** Cloud sandboxes moved onto the
  `egg-sandbox-v1` image with Claude Code and Node 22 baked in, so a boot
  spends no time downloading them, and commands carry an explicit timeout —
  Firecracker cuts one at 30 seconds without it. Local deploys wait out a
  full cold boot (~72s) rather than timing out at 60 and dropping the
  half-booted VM.
- **Egg Mode covers the bar on a plain desktop.** A solid-colour desktop has
  no wallpaper file to read, and macOS can keep showing a cached picture
  whose original is gone. Either way the cover was built and never shown:
  the HUD appeared, the menu bar stayed, and the mode looked like it had
  ignored the click. The strip now goes up regardless, and says once why it
  is plain and where Screen Recording access lives.
