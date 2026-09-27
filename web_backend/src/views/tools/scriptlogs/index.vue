<script setup>
import { onMounted, ref } from 'vue'
import { NInput, NSelect, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '脚本执行日志' })

const $table = ref(null)
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)

  const pad = (num) => num.toString().padStart(2, '0')

  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 获取当天的开始时间的时间戳
function getStartOfDayTimestamp() {
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  return now.getTime()
}

// 获取当天的结束时间的时间戳
function getEndOfDayTimestamp() {
  const now = new Date()
  now.setHours(23, 59, 59, 999)
  return now.getTime()
}

const startOfDayTimestamp = getStartOfDayTimestamp()
const endOfDayTimestamp = getEndOfDayTimestamp()

queryItems.value.start_time = formatTimestamp(startOfDayTimestamp)
queryItems.value.end_time = formatTimestamp(endOfDayTimestamp)

const datetimeRange = ref([startOfDayTimestamp, endOfDayTimestamp])
const handleDateRangeChange = (value) => {
  if (value == null) {
    queryItems.value.start_time = null
    queryItems.value.end_time = null
  } else {
    queryItems.value.start_time = formatTimestamp(value[0])
    queryItems.value.end_time = formatTimestamp(value[1])
  }
}

const levelOptions = [
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'DEBUG', value: 'DEBUG' },
]

function getLevelColor(level) {
  const colors = {
    INFO: 'blue',
    WARNING: 'orange',
    ERROR: 'red',
    DEBUG: 'green',
  }
  return colors[level] || 'default'
}

const columns = [
  {
    title: '执行时间',
    key: 'time',
    width: 180,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '日志级别',
    key: 'level',
    width: 100,
    align: 'center',
    render: (row) => {
      return h(NTag, { type: getLevelColor(row.level), size: 'small' }, { default: () => row.level })
    },
  },
  {
    title: 'IP地址',
    key: 'ip',
    width: 140,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'MAC地址',
    key: 'mac',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '用户名',
    key: 'username',
    width: 120,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '操作系统',
    key: 'os',
    width: 120,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '内核版本',
    key: 'kernel',
    width: 140,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '日志信息',
    key: 'info',
    minWidth: 200,
    align: 'left',
    ellipsis: { tooltip: true },
  },
  {
    title: '执行命令',
    key: 'cmd',
    minWidth: 200,
    align: 'left',
    ellipsis: { tooltip: true },
  },
  {
    title: '记录时间',
    key: 'created_at',
    width: 180,
    align: 'center',
    ellipsis: { tooltip: true },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getScriptLogList"
    >
      <template #queryBar>
        <QueryBarItem label="日志级别" :label-width="70">
          <NSelect
            v-model:value="queryItems.level"
            style="width: 180px"
            :options="levelOptions"
            clearable
            placeholder="请选择日志级别"
          />
        </QueryBarItem>
        <QueryBarItem label="IP地址" :label-width="70">
          <NInput
            v-model:value="queryItems.ip"
            clearable
            type="text"
            placeholder="请输入IP地址"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="用户名" :label-width="70">
          <NInput
            v-model:value="queryItems.username"
            clearable
            type="text"
            placeholder="请输入用户名"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="关键词" :label-width="70">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            type="text"
            placeholder="搜索日志信息"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="执行时间" :label-width="70">
          <NDatePicker
            v-model:value="datetimeRange"
            type="datetimerange"
            clearable
            placeholder="请选择时间范围"
            @update:value="handleDateRangeChange"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
