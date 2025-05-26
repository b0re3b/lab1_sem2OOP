<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="closeModal"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        @click="closeModal"
      ></div>

      <!-- Modal -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div
          :class="[
            'relative bg-white rounded-lg shadow-xl transform transition-all',
            sizeClasses,
            'max-h-[90vh] overflow-y-auto'
          ]"
          @click.stop
        >
          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900">
              {{ title }}
            </h3>
            <button
              @click="closeModal"
              class="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="px-6 py-4">
            <slot></slot>
          </div>

          <!-- Footer (optional) -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { computed, watch } from 'vue'

export default {
  name: 'SimpleModal',
  emits: ['update:modelValue', 'close'],
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      required: true
    },
    size: {
      type: String,
      default: 'md',
      validator: (value) => ['sm', 'md', 'lg', 'xl', '2xl'].includes(value)
    },
    closable: {
      type: Boolean,
      default: true
    },
    persistent: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const sizeClasses = computed(() => {
      const sizes = {
        sm: 'w-full max-w-md',
        md: 'w-full max-w-lg',
        lg: 'w-full max-w-2xl',
        xl: 'w-full max-w-4xl',
        '2xl': 'w-full max-w-6xl'
      }
      return sizes[props.size]
    })

    const closeModal = () => {
      if (!props.closable && !props.persistent) return

      emit('update:modelValue', false)
      emit('close')
    }

    // Обробка клавіші Escape
    const handleKeydown = (event) => {
      if (event.key === 'Escape' && props.modelValue && props.closable) {
        closeModal()
      }
    }

    // Блокування прокручування body коли модал відкритий
    watch(() => props.modelValue, (isOpen) => {
      if (isOpen) {
        document.body.style.overflow = 'hidden'
        document.addEventListener('keydown', handleKeydown)
      } else {
        document.body.style.overflow = ''
        document.removeEventListener('keydown', handleKeydown)
      }
    })

    return {
      sizeClasses,
      closeModal
    }
  }
}
</script>
