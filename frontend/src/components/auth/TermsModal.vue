<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div 
        v-if="isOpen" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="close"
      >
        <div 
          class="w-full max-w-lg max-h-[85vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-white/10"
          style="background: var(--color-surface);"
        >
          <!-- Header -->
          <div class="p-5 border-b border-gray-200/20 flex justify-between items-center shrink-0">
            <h2 class="text-lg font-semibold" style="color: var(--color-text-primary);">
              Aura Terms and Conditions
            </h2>
            <button 
              @click="close"
              class="p-1 rounded-full hover:bg-gray-500/10 transition-colors"
              style="color: var(--color-text-secondary);"
            >
              <XIcon class="w-5 h-5" />
            </button>
          </div>

          <!-- Body (Scrollable) -->
          <div class="p-5 overflow-y-auto flex-1 font-[Manrope] text-sm space-y-4" style="color: var(--color-text-secondary);">
            <p>These Terms and Conditions govern access to and use of the Aura platform by students, faculty, staff, administrators, governance officers, institutions, and other authorized users.</p>
            <p>By registering for, accessing, or using Aura, you agree to be bound by these Terms and Conditions.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">NATURE OF THE SERVICE</h3>
            <p>Aura is a software platform intended to facilitate attendance management, identity verification, geofenced attendance validation, scheduling, dashboards, analytics, governance workflows, and related institutional functions.</p>
            <p>Aura is provided subject to institutional configuration, user role, school policy, and applicable law.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">ELIGIBILITY AND AUTHORITY</h3>
            <p>You may use Aura only if:</p>
            <ul class="list-disc pl-5 space-y-1">
              <li>you are an authorized user of a participating institution or organization,</li>
              <li>the information you provide is true, accurate, current, and complete,</li>
              <li>and you have the legal capacity to agree to these Terms and Conditions, or a lawful representative has agreed on your behalf where required.</li>
            </ul>
            <p>If you are using Aura on behalf of a school, department, organization, or institution, you represent that you are authorized to bind that entity.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">ACCOUNT RESPONSIBILITY</h3>
            <p>You are responsible for:</p>
            <ul class="list-disc pl-5 space-y-1">
              <li>maintaining the confidentiality of your login credentials,</li>
              <li>restricting unauthorized access to your account,</li>
              <li>promptly reporting suspected misuse, compromise, or unauthorized activity,</li>
              <li>and ensuring that any information you submit through Aura is accurate and lawful.</li>
            </ul>
            <p>You must not share your account with unauthorized users or attempt to bypass role-based access controls.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">FACE REGISTRATION AND IDENTITY VERIFICATION</h3>
            <p>Where enabled, Aura may require face registration, face verification, or similar identity validation features for attendance or security purposes.</p>
            <p>By using these features, you acknowledge and agree that:</p>
            <ul class="list-disc pl-5 space-y-1">
              <li>your face image, scan, or face embedding may be processed for attendance verification and security,</li>
              <li>Aura may compare submitted facial data against registered data to confirm identity or detect misuse,</li>
              <li>false registration, impersonation, spoofing, or the use of another person’s image, device, or credentials is strictly prohibited,</li>
              <li>and failure or refusal to complete required verification steps may limit access to certain features.</li>
            </ul>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">LOCATION AND GEOFENCE FEATURES</h3>
            <p>Where location-enabled attendance is required, you acknowledge and agree that Aura may access device location data to verify attendance eligibility within authorized areas.</p>
            <p>You agree not to falsify, spoof, manipulate, proxy, or otherwise interfere with device location data, geofence controls, or attendance verification mechanisms.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">ACCEPTABLE USE</h3>
            <p>You agree not to:</p>
            <ul class="list-disc pl-5 space-y-1">
              <li>use Aura for unlawful, fraudulent, abusive, defamatory, or unauthorized purposes,</li>
              <li>impersonate another person or misrepresent your identity, affiliation, attendance, or authority,</li>
              <li>upload malicious code, interfere with security, or attempt unauthorized system access,</li>
              <li>scrape, copy, reverse engineer, or exploit the platform beyond permitted use,</li>
              <li>access data, reports, or dashboards beyond your role or authorization,</li>
              <li>use facial or location features for harassment, surveillance abuse, or unauthorized tracking,</li>
              <li>or circumvent technical, privacy, or security safeguards.</li>
            </ul>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">INSTITUTIONAL CONTROL AND ROLE-BASED ACCESS</h3>
            <p>Certain parts of Aura are configured and controlled by the institution that deploys the platform. Visibility of dashboards, analytics, attendance records, sanctions, and governance tools depends on role, institutional settings, and authorization.</p>
            <p>Institutions may suspend, limit, or revoke user access consistent with policy, governance requirements, contractual rights, or legal obligations.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">DATA ACCURACY AND USER RESPONSIBILITIES</h3>
            <p>You are responsible for ensuring that the data you submit is accurate, lawful, and not misleading.</p>
            <p>Aura may rely on user-submitted data, institutional imports, attendance logs, face verification, and location validation. Aura does not guarantee that all data will always be error-free, uninterrupted, or available in every circumstance.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">AVAILABILITY AND SERVICE CHANGES</h3>
            <p>Aura may update, improve, suspend, or discontinue features, modules, interfaces, workflows, or integrations at any time, with or without prior notice where reasonably necessary for maintenance, security, legal compliance, or operational reasons.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">INTELLECTUAL PROPERTY</h3>
            <p>All software, designs, workflows, trademarks, text, graphics, code, interfaces, and related materials forming part of Aura are owned by or licensed to Aura Project and are protected by applicable intellectual property laws.</p>
            <p>Except as expressly allowed, no user acquires ownership rights in Aura by using the platform.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">SUSPENSION AND TERMINATION</h3>
            <p>Aura or the relevant institution may suspend, restrict, or terminate access if:</p>
            <ul class="list-disc pl-5 space-y-1">
              <li>these Terms and Conditions are violated,</li>
              <li>use presents security, legal, or institutional risk,</li>
              <li>fraud, spoofing, impersonation, or misuse is suspected,</li>
              <li>an account becomes inactive, unauthorized, or no longer institutionally valid,</li>
              <li>or continued access is no longer operationally or legally appropriate.</li>
            </ul>
            <p>Termination does not extinguish obligations that by nature should survive, including privacy, confidentiality, liability, intellectual property, and dispute provisions.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">DISCLAIMERS</h3>
            <p>Aura is provided on an as available and as is basis, subject to maintenance, technical limitations, third-party dependencies, connectivity issues, and institutional configuration.</p>
            <p>To the fullest extent allowed by law, Aura does not warrant uninterrupted operation, perfect facial recognition, exact geolocation accuracy, or error-free availability at all times.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">LIMITATION OF LIABILITY</h3>
            <p>To the maximum extent permitted by law, Aura, its affiliates, officers, employees, contractors, licensors, and service providers shall not be liable for indirect, incidental, special, consequential, punitive, or exemplary damages arising from or related to the use of Aura.</p>
            <p>Nothing in these Terms and Conditions excludes liability that cannot lawfully be excluded under applicable law.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">INDEMNITY</h3>
            <p>You agree to indemnify and hold harmless Aura and its related parties from claims, losses, liabilities, damages, costs, and expenses arising from your violation of these Terms and Conditions, misuse of Aura, unlawful conduct, or infringement of the rights of others.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">PRIVACY</h3>
            <p>Your use of Aura is also governed by the Aura Privacy Policy. In the event of inconsistency, the Privacy Policy governs matters specifically relating to personal data processing, while these Terms and Conditions govern platform use and contractual obligations.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">GOVERNING LAW AND VENUE</h3>
            <p>These Terms and Conditions shall be governed by the laws of the Republic of the Philippines, without prejudice to mandatory rights granted by applicable law.</p>
            <p>Any dispute arising from or relating to these Terms and Conditions shall be brought before the proper courts of the Philippines, unless otherwise required by law or valid written agreement.</p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">CONTACT INFORMATION</h3>
            <p>For legal, contractual, or support concerns, please contact: <a href="mailto:auraautomessage@gmail.com" class="text-blue-500 hover:underline">auraautomessage@gmail.com</a></p>

            <h3 class="font-semibold text-[15px] mt-6" style="color: var(--color-text-primary);">CONSENT TO PRIVACY POLICY AND BIOMETRIC AND LOCATION PROCESSING</h3>
            <p>By creating or using my Aura account, I confirm that I have read and understood the Aura Privacy Policy and Terms and Conditions. I consent to the collection and processing of my personal data, including my profile information, attendance records, facial image or face embedding for identity verification, and location data for geofence-based attendance validation, when applicable, for the purposes stated in the Privacy Policy.</p>
            <p>If I am a minor or otherwise not legally capable of giving consent, such consent shall be given by my parent, guardian, or lawful representative where required by law.</p>
            <p>I also confirm that the information I provide in Aura is true, accurate, and complete, and that I will use the platform only for authorized and lawful purposes.</p>
          </div>

          <!-- Footer -->
          <div class="p-5 border-t border-gray-200/20 shrink-0 flex justify-end gap-3">
            <BaseButton
              variant="primary"
              size="md"
              @click="close"
            >
              I Understand
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { X as XIcon } from 'lucide-vue-next'
import BaseButton from '@/components/ui/BaseButton.vue'

defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close'])

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
