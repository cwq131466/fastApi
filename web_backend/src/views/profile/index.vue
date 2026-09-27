<script setup>
import { ref, computed } from 'vue'
import { NButton, NForm, NFormItem, NInput, NTabPane, NTabs, NImage, NIcon } from 'naive-ui'
import { CloudUploadOutlined } from '@vicons/antd'
import { useI18n } from 'vue-i18n'
import CommonPage from '@/components/page/CommonPage.vue'
import { useUserStore } from '@/store'
import api from '@/api'
import { getAvatarUrl } from '@/utils/avatar'

const { t } = useI18n()
const userStore = useUserStore()
const isLoading = ref(false)
const uploadingAvatar = ref(false)
const fileInputRef = ref(null)

// 用户信息的表单
const infoFormRef = ref(null)
const infoForm = ref({
  avatar: userStore.avatar,
  username: userStore.name,
  email: userStore.email,
})

// 计算显示的头像（自定义或默认）
const displayAvatar = computed(() => {
  return getAvatarUrl(infoForm.value.avatar, infoForm.value.username)
})

async function updateProfile() {
  isLoading.value = true
  infoFormRef.value?.validate(async (err) => {
    if (err) return
    await api
      .updateUser({ ...infoForm.value, id: userStore.userId })
      .then(() => {
        userStore.setUserInfo(infoForm.value)
        isLoading.value = false
        $message.success(t('common.text.update_success'))
      })
      .catch(() => {
        isLoading.value = false
      })
  })
}
const infoFormRules = {
  username: [
    {
      required: true,
      message: t('views.profile.message_username_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

// 处理头像文件选择
function handleAvatarSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    $message.error(t('views.profile.message_invalid_image_type'))
    return
  }
  
  // 验证文件大小（2MB）
  const maxSize = 2 * 1024 * 1024
  if (file.size > maxSize) {
    $message.error(t('views.profile.message_avatar_size_exceeded'))
    return
  }
  
  // 显示确认对话框
  $dialog.info({
    title: t('views.profile.label_confirm_upload'),
    content: t('views.profile.text_confirm_upload_avatar'),
    positiveText: t('common.buttons.confirm'),
    negativeText: t('common.buttons.cancel'),
    onPositiveClick: () => uploadAvatarFile(file)
  })
}

// 上传头像文件到服务器
async function uploadAvatarFile(file) {
  uploadingAvatar.value = true
  
  try {
    const res = await api.uploadAvatar(file)
    
    if (res.code === 200 || res.success) {
      // 更新本地表单和用户存储
      infoForm.value.avatar = res.data.url
      userStore.setUserInfo({ avatar: res.data.url })
      
      $message.success(t('views.profile.message_avatar_upload_success'))
    } else {
      throw new Error(res.msg || 'Upload failed')
    }
  } catch (error) {
    console.error('Avatar upload error:', error)
    $message.error(error.message || t('views.profile.message_avatar_upload_failed'))
  } finally {
    uploadingAvatar.value = false
    // 重置文件输入
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

// 触发文件选择器
function triggerAvatarUpload() {
  fileInputRef.value?.click()
}

// 修改密码的表单
const passwordFormRef = ref(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

async function updatePassword() {
  isLoading.value = true
  passwordFormRef.value?.validate(async (err) => {
    if (!err) {
      const data = { ...passwordForm.value, id: userStore.userId }
      await api
        .updatePassword(data)
        .then((res) => {
          $message.success(res.msg)
          passwordForm.value = {
            old_password: '',
            new_password: '',
            confirm_password: '',
          }
          isLoading.value = false
        })
        .catch(() => {
          isLoading.value = false
        })
    }
  })
}
const passwordFormRules = {
  old_password: [
    {
      required: true,
      message: t('views.profile.message_old_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  new_password: [
    {
      required: true,
      message: t('views.profile.message_new_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirm_password: [
    {
      required: true,
      message: t('views.profile.message_password_confirmation_required'),
      trigger: ['input', 'blur'],
    },
    {
      validator: validatePasswordStartWith,
      message: t('views.profile.message_password_confirmation_diff'),
      trigger: 'input',
    },
    {
      validator: validatePasswordSame,
      message: t('views.profile.message_password_confirmation_diff'),
      trigger: ['blur', 'password-input'],
    },
  ],
}
function validatePasswordStartWith(rule, value) {
  return (
    !!passwordForm.value.new_password &&
    passwordForm.value.new_password.startsWith(value) &&
    passwordForm.value.new_password.length >= value.length
  )
}
function validatePasswordSame(rule, value) {
  return value === passwordForm.value.new_password
}
</script>

<template>
  <CommonPage :show-header="false">
    <NTabs type="line" animated>
      <NTabPane name="website" :tab="$t('views.profile.label_modify_information')">
        <div class="m-30 flex items-center">
          <NForm
            ref="infoFormRef"
            label-placement="left"
            label-align="left"
            label-width="100"
            :model="infoForm"
            :rules="infoFormRules"
            class="w-400"
          >
            <NFormItem :label="$t('views.profile.label_avatar')" path="avatar">
              <div class="flex items-center gap-4">
                <!-- 头像显示 -->
                <NImage 
                  width="100" 
                  height="100" 
                  :src="displayAvatar"
                  object-fit="cover"
                  class="rounded-full border-2 border-gray-200"
                />
                
                <!-- 上传控件 -->
                <div class="flex flex-col gap-2">
                  <input
                    ref="fileInputRef"
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    class="hidden"
                    @change="handleAvatarSelect"
                  />
                  <NButton 
                    type="primary" 
                    size="small"
                    :loading="uploadingAvatar"
                    @click="triggerAvatarUpload"
                  >
                    <template #icon>
                      <NIcon><CloudUploadOutlined /></NIcon>
                    </template>
                    {{ $t('common.buttons.change_avatar') }}
                  </NButton>
                  <span class="text-xs text-gray-500">
                    {{ $t('views.profile.text_avatar_hint') }}
                  </span>
                </div>
              </div>
            </NFormItem>
            <NFormItem :label="$t('views.profile.label_username')" path="username">
              <NInput
                v-model:value="infoForm.username"
                type="text"
                :placeholder="$t('views.profile.placeholder_username')"
              />
            </NFormItem>
            <NFormItem :label="$t('views.profile.label_email')" path="email">
              <NInput
                v-model:value="infoForm.email"
                type="text"
                :placeholder="$t('views.profile.placeholder_email')"
              />
            </NFormItem>
            <NButton type="primary" :loading="isLoading" @click="updateProfile">
              {{ $t('common.buttons.update') }}
            </NButton>
          </NForm>
        </div>
      </NTabPane>
      <NTabPane name="contact" :tab="$t('views.profile.label_change_password')">
        <NForm
          ref="passwordFormRef"
          label-placement="left"
          label-align="left"
          :model="passwordForm"
          label-width="200"
          :rules="passwordFormRules"
          class="m-30 w-500"
        >
          <NFormItem :label="$t('views.profile.label_old_password')" path="old_password">
            <NInput
              v-model:value="passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_old_password')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_new_password')" path="new_password">
            <NInput
              v-model:value="passwordForm.new_password"
              :disabled="!passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_new_password')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_confirm_password')" path="confirm_password">
            <NInput
              v-model:value="passwordForm.confirm_password"
              :disabled="!passwordForm.new_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_confirm_password')"
            />
          </NFormItem>
          <NButton type="primary" :loading="isLoading" @click="updatePassword">
            {{ $t('common.buttons.update') }}
          </NButton>
        </NForm>
      </NTabPane>
    </NTabs>
  </CommonPage>
</template>
