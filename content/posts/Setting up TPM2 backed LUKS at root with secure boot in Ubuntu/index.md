---
title: "Setting up TPM2 backed LUKS at root with secure boot in Ubuntu"
date: 2025-02-28T00:00:00+02:00
draft: false
tags: ["sdboot", "Homelab", "LUKS", "TPM", "Foxware"]
author: "Roxedus"
ShowToc: true
cover:
  image: "images/drive.jpg"
  alt: "Hard disk with a padlock behind it"
  source: https://www.stockvault.net/photo/148555/hard-disk-drive
---

As part of a new homeserver build I plan to finish this year, I wanted to look into where the ecosystem is regarding LUKS volumes unlocked by TPM. This was sparked from how seamless it was when I set up my framework last year.

I gave my self a few conditions for this setup I would like to meet.
The first one is Secure boot, it's 2025, I should be able to do this by now, I also became aware of tooling that makes this easier.
I would like this setup to use sdboot, for really no particular reason than to try something else than grub. If I could fulfill this, UKI could also be a additional implementation detail.

I decided to use Ubuntu for this. Ubuntu 24.04 supports setting up LUKS on root as part of its installer, I used that for the initial LUKS setup.

## Replacing grub with sdboot

I based this from this [Gist comment](https://gist.github.com/gdamjan/ccdcda2c91119406a0f8d22f8b8f2c4a?permalink_comment_id=5210824#gistcomment-5210824)

This also installs the requisites for creating a Unified Kernel Image with TPM support

```sh
sudo apt purge -y --allow-remove-essential grub2-common grub-pc-bin grub-pc grub-gfxpayload-lists grub-efi-amd64-bin grub-efi-amd64-signed grub-common os-prober shim-signed libfreetype6
sudo apt-get autoremove -y --purge
sudo apt-mark hold "grub*"
sudo apt -y install systemd-boot systemd-ukify tpm2-tools libtss2-esys-3.0.2-0 libtss2-rc0t64 dracut
```

---

The dependency chain for `libtss2-esys` does not include the required sysusers files to create the tss account in the initramfs. This should have been resolved in this [commit](https://github.com/tpm2-software/tpm2-tss/pull/1582), but I can only assume the configure script used in debian/ubuntu is not set up to output these (which Arch has [done](https://gitlab.archlinux.org/archlinux/packaging/packages/tpm2-tss/-/blob/4.0.1-1/PKGBUILD?ref_type=tags#L38)). Therefore we have to grab this manually.

```sh
sudo curl -o /usr/lib/sysusers.d/tpm2-tss.conf https://raw.githubusercontent.com/tpm2-software/tpm2-tss/refs/heads/master/dist/sysusers.d/tpm2-tss.conf
```

---

Now it's time to reboot, we should now be booting with sdboot, as the `systemd-boot` package also installed the bootloader into the EFI partition previously used by grub. We can confirm the bootloader with `bootctl`, looking at the product under the current boot loader entry.

---

## Secure Boot

With a touch of FoxWare we can easily achieve Secure Boot. The goal here is to run our own secure boot certificate, and sign the kernel ourself.

I use [sbctl](https://github.com/Foxboron/sbctl) for this, as it makes the whole setup painless. It is not currently packed for the default debian/ubuntu repositories, but it is [getting there](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1030845). There is however a community package available in the meantime.

```sh
echo 'deb http://download.opensuse.org/repositories/home:/jloeser:/secureboot/xUbuntu_24.04/ /' | sudo tee /etc/apt/sources.list.d/home:jloeser:secureboot.list
curl -fsSL https://download.opensuse.org/repositories/home:jloeser:secureboot/xUbuntu_24.04/Release.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/home_jloeser_secureboot.gpg > /dev/null
sudo apt update
sudo apt install -y sbctl
# This is just to ensure the config file exist in the expected location
sudo mkdir -p /etc/sbctl
sudo touch /etc/sbctl/sbctl.conf
```

---

With sbctl installed, it is now time to create and enroll the needed keys for secure boot. This is just two commands with sbctl. *This assumes that your motherboard is already configured to be able to receive custom keys*

```sh
sudo sbctl create-keys
sudo sbctl enroll-keys
```

---

At this point we can run `sbctl verify` to get a list of entries detected in the bootloader. It should also note these are not currently signed. Now that we have enrolled keys, secure boot should not be in setup mode, and thus require images to be signed.

I like to sign all entries in the bootloader at this stage. I usually do that by assuming all entries are in a couple of directories in `/boot`.

```sh
for file in /boot/efi/*/*/linux /boot/efi/EFI/*/*.efi; do
  sudo sbctl sign -s $file
done
```

---

After verifying these are signed, it should now be safe to reboot. In this reboot, it is worth checking with the uefi that secure boot is enabled.

---

## Unified Kernel Image

Now that we have secure boot, as well as sdboot going, we can implement booting with a UKI. This allows us to use some of the measurements UKI booting does, to tie into cryptsetup and automatic LUKS unlocks.

The steps to make this happen differs a bit between versions. The difference might just boil down to me missing something, but my untested theory is that some package has moved the heavy lifting to `kernel-install`, as 24.10 also automatically signs the image with sbctl as well as sorting out the bootloader entry.

---

While writing this, I used both Ubuntu 24.10 and 24.04.

For both versions, I told Dracut to run with `hostonly`.

```sh
cat << EOF | sudo tee /etc/dracut.conf.d/hostonly.conf
hostonly="yes"
EOF
```

- For 24.10, only `kernel-install` needs to be told to create a UKI.

  ```sh
  cat << EOF | sudo tee /etc/kernel/install.conf
  layout=uki
  EOF
  ```

- For the current LTS, we need to tell Dracut to create a UKI with the option `--uefi`.

  ```sh
  cat << EOF | sudo tee /etc/dracut.conf.d/uefi.conf
  uefi="yes"
  EOF
  ```

  As mentioned above, my experience is that there is a couple of manual tasks left to do.

  - Sign the UKI
  - Tell the bootloader to use the UKI as the default entry.

    You can do this with `bootctl set-default` and pointing it to the entry matching the name Dracut built.

---

Now we add TPM support to the UKI, by telling Dracut to include the `tpm2-tss` module, as well as forcing a build.

```sh
sudo dracut -f --add tpm2-tss
```

Verify that the image is signed before rebooting.
To verify the UKI was used to boot, we can use `bootctl` and check that `TPM2 Support` and `Measured UKI` are true.

---

## TPM Backed LUKS

For this writeup I used somewhat relaxed measurements. The explanations are fetched from [UAPI](https://uapi-group.org/specifications/specs/linux_tpm_pcr_registry/).

- 0: Core system firmware executable code
- 2: Extended or pluggable executable code; includes option ROMs on pluggable hardware
- 7: SecureBoot state

While testing I used blkid to fetch the mount path or UUID of a device with LUKS set up. This substitution works if there is __only one LUKS device in the system__.

We can now enroll TPM2 as a keyslot for the LUKS partition.

```sh
sudo systemd-cryptenroll $(sudo blkid -o device --match-token TYPE=crypto_LUKS) --tpm2-device=auto --tpm2-pcrs=0,2,7
```

Since we use Dracut, we also need to set the crypttab. This line should probably be a sed, but while writing, the Ubuntu installer always set up the LUKS volume with the same name, and this was just easier.

```sh
cat << EOF | sudo tee /etc/crypttab
dm_crypt-0 UUID=$(sudo blkid -o value -s UUID --match-token TYPE=crypto_LUKS) none tpm2-device=auto,luks,tpm2-pcrs=0+2+7
EOF
```

We should now be able to reboot, without being prompted by the LUKS password.

---

### Updates

Depending on the measurements used, you might have to bind the keyslot again, with the new values of the measurement.

BIOS updates would change the value of PCR0, and thus require a setting the keyslot again.

The command is quite similar to the original enrollment, with the addition of telling it to wipe the previous tpm slot.

```sh
sudo systemd-cryptenroll $(sudo blkid -o device --match-token TYPE=crypto_LUKS) --tpm2-device=auto --tpm2-pcrs=0,2,7 --wipe-slot=tpm2
```
