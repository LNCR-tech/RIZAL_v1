<template>
  <div
    class="governance-workspace"
    :class="{ 'governance-workspace--focus': !showGovernanceTopBar }"
  >
    <TopBar
      v-if="showGovernanceTopBar"
      class="dashboard-enter dashboard-enter--1"
      :user="currentUser"
      :unread-count="0"
    />

    <div
      v-if="showWorkspaceTopRow"
      class="governance-top-row dashboard-enter dashboard-enter--2"
    >
      <div class="search-wrap">
        <div class="search-shell" :class="{ 'search-shell--expanded': searchActive }">
          <div class="search-input-row">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search workspaces..."
              class="search-input"
            />
            <span class="search-icon-wrap" aria-hidden="true">
              <Search :size="14" class="search-icon" style="color: var(--color-primary);" />
            </span>
          </div>

          <div class="search-results-panel">
            <div class="search-results-inner">
              <div v-if="isAiCreating" class="search-results-empty">
                <LoaderCircle :size="16" :stroke-width="2" class="governance-state-card__spinner" style="display: inline-block; margin-right: 8px; vertical-align: middle;" />
                <span style="vertical-align: middle;">AI is working...</span>
              </div>
              <div v-else-if="aiResult" class="search-results-list">
                <button
                  type="button"
                  class="search-result-item"
                  @click="router.push(aiResult.route)"
                  style="background: rgba(170, 255, 0, 0.1); border: 1px solid var(--color-primary);"
                >
                  <div class="search-result-icon">
                    <Sparkles :size="16" :stroke-width="2" style="color: var(--color-primary);" />
                  </div>
                  <div class="search-result-copy">
                    <strong>{{ aiResult.label }}</strong>
                    <span>{{ aiResult.sublabel }}</span>
                  </div>
                </button>
              </div>
              <div v-else-if="searchResults.length" class="search-results-list">
                <button
                  v-for="item in searchResults"
                  :key="item.id"
                  type="button"
                  class="search-result-item"
                  @click="handleSearchResultClick(item)"
                >
                  <div class="search-result-icon">
                    <component :is="item.icon" :size="16" :stroke-width="2" />
                  </div>
                  <div class="search-result-copy">
                    <strong>{{ item.label }}</strong>
                    <span>{{ item.sublabel }}</span>
                  </div>
                </button>
              </div>
              <div v-else class="search-results-empty">
                No results found for "{{ searchQuery }}"
              </div>
            </div>
          </div>
        </div>
      </div>

      <button
        type="button"
        class="governance-create-button"
        aria-label="Open governance create actions"
        @click="handleOpenCreateSheet"
      >
        <Plus :size="18" :stroke-width="2.1" />
        <span>Create</span>
      </button>
    </div>

    <section v-if="isWorkspaceLoading" class="governance-state-card dashboard-enter dashboard-enter--3">
      <LoaderCircle class="governance-state-card__spinner" :size="28" :stroke-width="2.2" />
      <p class="governance-state-card__title">Loading governance workspace</p>
      <p class="governance-state-card__copy">Syncing your unit data.</p>
    </section>

    <section
      v-else-if="workspaceError && !hasRenderableData"
      class="governance-state-card governance-state-card--error dashboard-enter dashboard-enter--3"
    >
      <AlertCircle :size="28" :stroke-width="2.1" />
      <p class="governance-state-card__title">Governance workspace unavailable</p>
      <p class="governance-state-card__copy">{{ workspaceError }}</p>
    </section>

    <template v-else>
      <template v-if="isOverviewSection">
        <template v-if="isEnhancedOverview">
          <section class="governance-summary-grid governance-summary-grid--ssg dashboard-enter dashboard-enter--3">
            <article
              v-for="card in ssgSummaryCards"
              :key="card.key"
              class="governance-card governance-card--stat governance-card--spotlight governance-card--stat-showcase"
              :class="[
                `governance-card--stat-showcase-${card.tone}`,
                card.position ? `governance-card--stat-showcase-${card.position}` : '',
              ]"
            >
              <div class="governance-stat-showcase__top">
                <div class="governance-stat-showcase__eyebrow">
                  <div class="governance-stat-showcase__icon">
                    <component :is="card.icon" :size="18" :stroke-width="2" />
                  </div>
                  <span>{{ card.label }}</span>
                </div>
              </div>

              <div class="governance-stat-showcase__copy">
                <strong>{{ card.value }}</strong>
              </div>
            </article>
          </section>

          <section class="governance-analytics-shell dashboard-enter dashboard-enter--4">
            <div class="governance-analytics-shell__header">
              <h2 class="governance-analytics-shell__title">Event Analytics</h2>

              <label
                v-if="analyticsEventOptions.length"
                class="governance-analytics-picker"
              >
                <span class="governance-event-select governance-event-select--primary">
                  <select
                    class="governance-event-select__input"
                    :value="selectedAnalyticsEventId || ''"
                    @change="setSelectedAnalyticsEventId($event.target.value)"
                  >
                    <option
                      v-for="option in analyticsEventOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <ChevronDown :size="16" :stroke-width="2" />
                </span>
              </label>
            </div>

            <div class="governance-analytics-stack">
              <article class="governance-card governance-card--health governance-card--health-showcase">
                <div class="governance-health-card__header">
                  <div class="governance-health-card__header-copy">
                    <p class="governance-health-card__label">Event Health</p>
                    <h2 class="governance-health-card__title">{{ eventHealthInsight.title }}</h2>
                  </div>

                  <div ref="reportMenuRef" class="governance-health-card__menu-wrap">
                    <button
                      type="button"
                      class="governance-health-card__menu"
                      :aria-expanded="isReportMenuOpen ? 'true' : 'false'"
                      aria-label="Open report actions"
                      @click="toggleReportMenu"
                    >
                      <MoreHorizontal :size="18" :stroke-width="2.2" />
                    </button>

                    <div v-if="isReportMenuOpen" class="governance-report-popover">
                      <button
                        type="button"
                        class="governance-report-popover__action governance-report-popover__action--primary"
                        :disabled="!canExportPar || isExportingPar"
                        @click="handleExportPar"
                      >
                        <FileText :size="16" :stroke-width="2" />
                        <span>{{ isExportingPar ? 'Preparing PAR...' : 'Export PAR' }}</span>
                      </button>

                      <button
                        type="button"
                        class="governance-report-popover__action"
                        :disabled="!canExportMasterlist || isExportingMasterlist"
                        @click="handleExportMasterlist"
                      >
                        <FileSpreadsheet :size="16" :stroke-width="2" />
                        <span>{{ isExportingMasterlist ? 'Preparing CSV...' : 'Export CSV' }}</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="governance-health-card__meta">
                  <span class="governance-health__state">
                    <span class="governance-health__state-dot" />
                    {{ eventHealthInsight.statusLabel }}
                  </span>
                  <span>{{ eventHealthInsight.eventDateLabel }}</span>
                </div>

                <div
                  class="governance-health-arc"
                  :aria-label="`${eventHealthInsight.title}: ${eventHealthInsight.valueLabel} capacity`"
                  role="img"
                >
                  <div class="governance-health-arc__badge">
                    <span class="governance-health-arc__badge-dot" />
                    <strong>{{ eventHealthInsight.secondaryValueLabel }}</strong>
                    <span>{{ eventHealthInsight.secondaryLabel }}</span>
                  </div>

                  <span
                    v-for="segment in eventHealthGaugeSegments"
                    :key="segment.key"
                    class="governance-health-arc__segment"
                    :class="{ 'is-active': segment.active }"
                    :style="segment.style"
                  />

                  <div class="governance-health-arc__center">
                    <strong class="governance-health-arc__value">{{ eventHealthInsight.valueLabel }}</strong>
                    <span class="governance-health-arc__caption">Capacity</span>
                  </div>
                </div>

                <div class="governance-health-card__tiles">
                  <article class="governance-health-card__tile">
                    <span>Attended</span>
                    <strong>{{ eventHealthInsight.attendedLabel }}</strong>
                  </article>

                  <article class="governance-health-card__tile">
                    <span>Target</span>
                    <strong>{{ eventHealthInsight.totalLabel }}</strong>
                  </article>
                </div>

                <p v-if="exportError" class="governance-report-error governance-report-error--inline">{{ exportError }}</p>
              </article>

              <article class="governance-card governance-card--chart">
                <GovernanceBreakdownBars
                  v-if="demographicInsight.items.length"
                  :title="demographicInsight.title"
                  :items="demographicInsight.items"
                />
                <article v-else class="governance-empty-card governance-empty-card--subtle">
                  <BarChart3 :size="18" :stroke-width="2" />
                  <div>
                    <strong>Waiting for richer attendance rows.</strong>
                  </div>
                </article>
              </article>

              <article class="governance-card governance-card--chart governance-card--arrival">
                <div class="governance-card__header governance-card__header--compact">
                  <div>
                    <h2 class="governance-card__title">Peak Arrival Time</h2>
                  </div>
                </div>

                <GovernanceArrivalBars
                  v-if="arrivalInsight.items.length"
                  :insight="arrivalInsight"
                />
                <article v-else class="governance-empty-card governance-empty-card--subtle">
                  <Clock3 :size="18" :stroke-width="2" />
                  <div>
                    <strong>No sign-in timestamps yet.</strong>
                  </div>
                </article>
              </article>
            </div>
          </section>

          <section class="governance-analytics-shell dashboard-enter dashboard-enter--5">
            <article class="governance-card governance-card--chart governance-card--timeline">
              <div class="governance-card__header">
                <div>
                  <p class="governance-card__eyebrow">Semester Arc</p>
                  <h2 class="governance-card__title">Engagement Over Time</h2>
                </div>
              </div>

              <GovernanceTrendChart
                v-if="engagementTimeline.points.length > 1"
                :points="engagementTimeline.points"
              />
              <article v-else class="governance-empty-card governance-empty-card--subtle">
                <TrendingUp :size="18" :stroke-width="2" />
                <div>
                  <strong>More reported events are needed for a trend line.</strong>
                </div>
              </article>
            </article>
          </section>

        </template>

        <section v-else class="governance-summary-grid dashboard-enter dashboard-enter--3">
          <article class="governance-card governance-card--engagement">
            <div class="governance-card__header">
              <div>
                <p class="governance-card__eyebrow">Analytics</p>
                <h2 class="governance-card__title">Engagement</h2>
              </div>
              <span v-if="reportsLoading" class="governance-card__status">Refreshing</span>
            </div>

            <div class="governance-card__engagement-body">
              <GovernanceProgressRing :percentage="engagementMetric.percentage">
                <strong class="governance-progress-copy__value">{{ engagementMetric.valueLabel }}</strong>
                <span class="governance-progress-copy__label">{{ engagementMetric.centerLabel }}</span>
              </GovernanceProgressRing>
            </div>
          </article>

          <article class="governance-card governance-card--stat">
            <div class="governance-stat-card__icon">
              <UsersRound :size="18" :stroke-width="2" />
            </div>
            <div class="governance-stat-card__copy">
              <strong>{{ activeStudentsMetric.valueLabel }}</strong>
              <p>Students in scope</p>
            </div>
          </article>

          <article class="governance-card governance-card--stat">
            <div class="governance-stat-card__icon">
              <CalendarDays :size="18" :stroke-width="2" />
            </div>
            <div class="governance-stat-card__copy">
              <strong>{{ eventVolumeMetric.valueLabel }}</strong>
              <p>Events this week</p>
            </div>
          </article>

          <article class="governance-card governance-card--stat">
            <div class="governance-stat-card__icon">
              <BellRing :size="18" :stroke-width="2" />
            </div>
            <div class="governance-stat-card__copy">
              <strong>{{ latestAnnouncementReachMetric.valueLabel }}</strong>
              <p>Announcement reach</p>
            </div>
          </article>
        </section>

        <section class="governance-zone dashboard-enter" :class="isEnhancedOverview ? 'dashboard-enter--7' : 'dashboard-enter--4'">
          <div class="governance-zone__header">
            <div>
              <p class="governance-zone__eyebrow">Needs Attention</p>
              <h2 class="governance-zone__title">Actionable follow-ups</h2>
            </div>
          </div>

          <div v-if="attentionItems.length" class="governance-attention-list">
            <button
              v-for="item in attentionItems"
              :key="item.key"
              type="button"
              class="governance-attention-card"
              :class="`governance-attention-card--${item.tone}`"
              @click="openAttentionItem(item)"
            >
              <div class="governance-attention-card__icon">
                <CircleAlert :size="18" :stroke-width="2.1" />
              </div>

              <div class="governance-attention-card__copy">
                <span class="governance-attention-card__eyebrow">{{ item.eyebrow }}</span>
                <strong>{{ item.title }}</strong>
              </div>

              <span class="governance-attention-card__action">{{ item.actionLabel }}</span>
            </button>
          </div>
          <article v-else class="governance-empty-card">
            <ShieldCheck :size="20" :stroke-width="2" />
            <div>
              <strong>Nothing urgent right now.</strong>
            </div>
          </article>
        </section>

        <section class="governance-zone dashboard-enter" :class="isEnhancedOverview ? 'dashboard-enter--8' : 'dashboard-enter--5'">
          <div class="governance-zone__header">
            <div>
              <p class="governance-zone__eyebrow">Up Next</p>
              <h2 class="governance-zone__title">Upcoming events</h2>
            </div>

            <button type="button" class="governance-inline-action" @click="openSection('events')">
              Open Events
              <ArrowRight :size="16" :stroke-width="2" />
            </button>
          </div>

          <div v-if="upcomingEvents.length" class="governance-event-carousel">
            <article
              v-for="event in upcomingEvents"
              :key="event.id"
              class="governance-event-card"
              :class="`governance-event-card--${getUpcomingEventTone(event)}`"
            >
              <div class="governance-event-card__top">
                <span class="governance-event-card__status">
                  {{ getUpcomingEventTone(event) === 'live' ? 'Live now' : getStatusLabel(event.status) }}
                </span>
                <span class="governance-event-card__scope">{{ event.scope_label || activeUnitName }}</span>
              </div>

              <strong class="governance-event-card__title">{{ event.name || 'Untitled event' }}</strong>
              <p class="governance-event-card__line">{{ event.location || 'Location pending' }}</p>

              <div class="governance-event-card__footer">
                <span class="governance-event-card__time">
                  <Clock3 :size="14" :stroke-width="2" />
                  {{ formatDateRange(event.start_datetime || event.start_time, event.end_datetime || event.end_time) }}
                </span>

                <button type="button" class="governance-event-card__button" @click.stop="openEvent(event)">
                  {{ getUpcomingEventActionLabel(event) }}
                </button>
              </div>
            </article>
          </div>
          <article v-else class="governance-empty-card">
            <CalendarDays :size="20" :stroke-width="2" />
            <div>
              <strong>No upcoming events.</strong>
            </div>
          </article>
        </section>

        <section class="governance-zone governance-zone--feed dashboard-enter" :class="isEnhancedOverview ? 'dashboard-enter--9' : 'dashboard-enter--6'">
          <div class="governance-zone__header">
            <div>
              <p class="governance-zone__eyebrow">Recent Announcements</p>
              <h2 class="governance-zone__title">Latest governance updates</h2>
            </div>
          </div>

          <div v-if="recentAnnouncements.length" class="governance-feed-list">
            <article
              v-for="announcement in recentAnnouncements"
              :key="announcement.id"
              class="governance-feed-card"
            >
              <div class="governance-feed-card__top">
                <div class="governance-feed-card__headline">
                  <strong>{{ announcement.title || 'Untitled announcement' }}</strong>
                  <span>{{ formatAnnouncementTime(announcement.created_at || announcement.updated_at) }}</span>
                </div>
                <span class="governance-feed-card__status">{{ getStatusLabel(announcement.status) }}</span>
              </div>

              <div class="governance-feed-card__meta">
                <span>{{ formatAnnouncementAudienceMeta(announcement) }}</span>
              </div>
            </article>
          </div>
          <article v-else class="governance-empty-card">
            <Megaphone :size="20" :stroke-width="2" />
            <div>
              <strong>No announcements yet.</strong>
            </div>
          </article>
        </section>
      </template>

      <section v-else-if="isEventsSection" class="governance-events dashboard-enter dashboard-enter--3">
        <template v-if="selectedEventForAttendance">
          <header class="governance-events__header">
            <div class="governance-events__header-copy" style="display: flex; gap: 12px; align-items: center;">
              <button
                type="button"
                style="display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 50%; background: none; border: none; cursor: pointer; color: var(--color-text);"
                @click="closeAttendanceSheet"
                aria-label="Back to event feed"
              >
                <ArrowRight :size="20" :stroke-width="2.3" style="transform: rotate(180deg);" />
              </button>
              <h1 class="governance-events__title">{{ selectedEventForAttendance.name || 'Event Directory' }}</h1>
            </div>
          </header>

          <div class="governance-directory">
            <div v-if="attendanceDirectoryFilters.length" class="governance-directory__filters">
              <button
                v-for="filter in attendanceDirectoryFilters"
                :key="filter.value"
                type="button"
                class="governance-directory__filter"
                :class="{ 'governance-directory__filter--active': attendanceDirectoryFilter === filter.value }"
                :aria-pressed="attendanceDirectoryFilter === filter.value ? 'true' : 'false'"
                :aria-label="`${filter.label} (${filter.count})`"
                @click="setAttendanceDirectoryFilter(filter.value)"
              >
                {{ filter.label }}
              </button>
            </div>

            <div class="governance-directory__list">
              <div
                v-for="row in selectedEventAttendanceRows"
                :key="row.key"
                class="governance-directory__item"
              >
                <div class="governance-directory__avatar">
                  <UsersRound :size="16" />
                </div>
                <div class="governance-directory__info">
                  <strong class="governance-directory__name">{{ row.studentName }}</strong>
                  <p class="governance-directory__meta">{{ getAttendanceDirectoryMeta(row) }}</p>
                </div>
                <span
                  class="governance-directory__status"
                  :class="`governance-directory__status--${row.statusCategory}`"
                >
                  {{ row.statusLabel }}
                </span>
              </div>

              <div v-if="selectedEventAttendanceRows.length === 0" class="governance-empty-card governance-empty-card--subtle">
                <UsersRound :size="18" :stroke-width="2" />
                <div>
                  <strong>No students found for this scope.</strong>
                </div>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <header class="governance-events__header">
          <div class="governance-events__header-copy">
            <h1 class="governance-events__title">Events</h1>
          </div>

          <button
            type="button"
            class="governance-events__create-button"
            aria-label="Open event and announcement create options"
            @click="handleOpenCreateSheet"
          >
            <Plus :size="22" :stroke-width="2.3" />
          </button>
        </header>

        <div
          class="governance-events__toggle"
          role="tablist"
          aria-label="Choose which event feed to show"
        >
          <button
            type="button"
            class="governance-events__toggle-button"
            :class="{ 'governance-events__toggle-button--active': eventFeedMode === 'council' }"
            :aria-selected="eventFeedMode === 'council' ? 'true' : 'false'"
            @click="setEventFeedMode('council')"
          >
            <Building2 :size="16" :stroke-width="2" />
            <span>Council</span>
          </button>

          <button
            type="button"
            class="governance-events__toggle-button"
            :class="{ 'governance-events__toggle-button--active': eventFeedMode === 'campus' }"
            :aria-selected="eventFeedMode === 'campus' ? 'true' : 'false'"
            @click="setEventFeedMode('campus')"
          >
            <GraduationCap :size="16" :stroke-width="2" />
            <span>Campus</span>
          </button>
        </div>

        <section
          v-if="isActiveEventsFeedLoading"
          class="governance-state-card"
        >
          <LoaderCircle class="governance-state-card__spinner" :size="24" :stroke-width="2.2" />
          <p class="governance-state-card__title">Loading events</p>
          <p class="governance-state-card__copy">Pulling the latest {{ eventFeedModeLabel.toLowerCase() }} feed.</p>
        </section>

        <section
          v-else-if="activeEventsFeedError && !selectedFeedEvents.length"
          class="governance-state-card governance-state-card--error"
        >
          <AlertCircle :size="24" :stroke-width="2.1" />
          <p class="governance-state-card__title">Unable to load {{ eventFeedModeLabel.toLowerCase() }} feed</p>
          <p class="governance-state-card__copy">{{ activeEventsFeedError }}</p>
        </section>

        <template v-else>
          <section class="governance-events__calendar-card">
            <div class="governance-events__calendar-head">
              <div>
                <span class="governance-events__calendar-eyebrow">{{ eventFeedModeLabel }}</span>
                <h2 class="governance-events__calendar-title">{{ calendarMonthLabel }}</h2>
              </div>

              <div class="governance-events__calendar-nav">
                <button
                  type="button"
                  class="governance-events__calendar-nav-button"
                  aria-label="Previous month"
                  @click="shiftCalendarMonth(-1)"
                >
                  <ChevronDown :size="16" :stroke-width="2.1" class="governance-events__calendar-nav-icon governance-events__calendar-nav-icon--prev" />
                </button>

                <button
                  type="button"
                  class="governance-events__calendar-nav-button"
                  aria-label="Next month"
                  @click="shiftCalendarMonth(1)"
                >
                  <ChevronDown :size="16" :stroke-width="2.1" class="governance-events__calendar-nav-icon governance-events__calendar-nav-icon--next" />
                </button>
              </div>
            </div>

            <div class="governance-events__calendar-weekdays">
              <span v-for="weekday in calendarWeekdayLabels" :key="weekday">{{ weekday }}</span>
            </div>

            <div class="governance-events__calendar-grid">
              <button
                v-for="day in calendarDays"
                :key="day.key"
                type="button"
                class="governance-events__calendar-day"
                :class="{
                  'governance-events__calendar-day--outside': !day.isCurrentMonth,
                  'governance-events__calendar-day--today': day.isToday,
                  'governance-events__calendar-day--selected': day.isSelected,
                  'governance-events__calendar-day--has-events': day.eventCount > 0,
                }"
                @click="selectCalendarDay(day)"
              >
                <span class="governance-events__calendar-day-number">{{ day.dayNumber }}</span>
                <span v-if="day.eventCount > 0" class="governance-events__calendar-day-count">{{ day.eventCount }}</span>
                <span v-else class="governance-events__calendar-day-spacer" aria-hidden="true"></span>
              </button>
            </div>
          </section>

          <section class="governance-events__list-section">
            <div class="governance-events__section-header">
              <div>
                <h2 class="governance-events__section-title">{{ eventListTitle }}</h2>
                <span class="governance-events__section-meta">
                  {{ calendarEventFeedList.length }} shown
                </span>
              </div>
            </div>

            <div
              v-if="selectedFeedEvents.length"
              class="governance-events__filters"
              role="tablist"
              aria-label="Filter events by status"
            >
              <button
                v-for="filter in eventFeedFilters"
                :key="filter.value"
                type="button"
                class="governance-events__filter-pill"
                :class="{ 'governance-events__filter-pill--active': eventListFilter === filter.value }"
                :aria-selected="eventListFilter === filter.value ? 'true' : 'false'"
                @click="setEventListFilter(filter.value)"
              >
                <span>{{ filter.label }}</span>
                <strong>{{ filter.count }}</strong>
              </button>
            </div>

            <div v-if="calendarEventFeedList.length" class="governance-events__list">
              <div
                v-for="event in calendarEventFeedList"
                :key="event.id"
                class="governance-events__swipe"
                :class="{ 'governance-events__swipe--open': canSwipeEditEvents && isGovernanceEventSwipeOpen(event.id) }"
              >
                <div v-if="canSwipeEditEvents" class="governance-events__row-actions">
                  <button
                    type="button"
                    class="governance-events__row-action governance-events__row-action--edit"
                    :disabled="isEventEditorSaving"
                    aria-label="Edit event"
                    @pointerdown.stop
                    @click.stop="editManagedEvent(event)"
                  >
                    <Edit2 :size="18" :stroke-width="2" />
                  </button>
                </div>

                <article
                  class="governance-events__row"
                  :style="canSwipeEditEvents ? getGovernanceEventSwipeStyle(event.id) : undefined"
                  @pointerdown="canSwipeEditEvents ? onGovernanceEventPointerDown(event.id, $event) : null"
                  @pointermove="canSwipeEditEvents ? onGovernanceEventPointerMove(event.id, $event) : null"
                  @pointerup="canSwipeEditEvents ? onGovernanceEventPointerEnd(event.id, $event) : null"
                  @pointercancel="canSwipeEditEvents ? onGovernanceEventPointerCancel(event.id, $event) : null"
                  @lostpointercapture="canSwipeEditEvents ? onGovernanceEventPointerCancel(event.id, $event) : null"
                >
                  <div 
                    class="governance-events__row-head" 
                    @click="openAttendanceSheet(event)"
                    style="cursor: pointer;"
                  >
                    <span class="governance-events__row-icon">
                      <Clock3 :size="18" :stroke-width="2" />
                    </span>

                    <div class="governance-events__row-copy">
                      <strong>{{ event.name || 'Untitled event' }}</strong>
                      <span class="governance-events__row-meta">
                        {{ getEventAudienceLabel(event, eventFeedMode) }} ·
                        {{ formatEventRangeCompact(event) }}
                      </span>
                      <span class="governance-events__row-state-line">
                        <span
                          class="governance-events__row-state-dot"
                          :class="`governance-events__row-state-dot--${resolveEventFeedState(event)}`"
                        />
                        {{ getEventFeedStateLabel(event) }}
                      </span>
                    </div>

                    <button
                      type="button"
                      class="governance-events__expand"
                      :aria-expanded="isEventExpanded(event.id) ? 'true' : 'false'"
                      :aria-label="isEventExpanded(event.id) ? 'Hide metrics' : 'Show metrics'"
                      @pointerdown.stop
                      @click.stop="toggleEventExpanded(event.id)"
                    >
                      <ChevronDown
                        :size="18"
                        :stroke-width="2.1"
                        :class="{ 'governance-events__expand-icon--open': isEventExpanded(event.id) }"
                      />
                    </button>
                  </div>

                  <div v-if="isEventExpanded(event.id)" class="governance-events__row-details" @click.stop>
                    <div class="governance-events__detail-metrics">
                      <article class="governance-events__detail-metric">
                        <span>Checked In</span>
                        <strong>{{ getEventCardSnapshot(event).checkedInLabel }}</strong>
                      </article>

                      <article class="governance-events__detail-metric">
                        <span>Checked Out</span>
                        <strong>{{ getEventCardSnapshot(event).checkedOutLabel }}</strong>
                      </article>
                    </div>

                    <div class="governance-events__detail-actions">
                      <button
                        type="button"
                        class="governance-events__detail-button governance-events__detail-button--primary"
                        :disabled="!getEventCardSnapshot(event).canExportPar || isExportingPar"
                        @click.stop="handleExportEventPar(event)"
                      >
                        {{ isExportingPar ? 'Preparing PAR...' : 'Export Par' }}
                      </button>

                      <button
                        type="button"
                        class="governance-events__detail-button"
                        :disabled="!getEventCardSnapshot(event).canExportMasterlist || isExportingMasterlist"
                        @click.stop="handleExportEventCsv(event)"
                      >
                        {{ isExportingMasterlist ? 'Preparing Csv...' : 'Export Csv' }}
                      </button>
                    </div>
                    <p v-if="exportError" class="governance-events__detail-error">{{ exportError }}</p>
                  </div>
                </article>
              </div>
            </div>
            <article v-else class="governance-empty-card governance-empty-card--subtle">
              <CalendarDays :size="18" :stroke-width="2" />
              <div>
                <strong>No events match this calendar view yet.</strong>
              </div>
            </article>
          </section>
        </template>
        </template>
      </section>

      <section v-else-if="isStudentsSection" class="governance-student-directory dashboard-enter dashboard-enter--3">
        <label class="governance-student-directory__search-shell">
          <Search :size="16" :stroke-width="2.2" />
          <input
            v-model="studentDirectoryQuery"
            type="text"
            class="governance-student-directory__search-input"
            :placeholder="studentDirectorySearchPlaceholder"
          />
        </label>

        <div
          v-if="studentDirectoryFilters.length"
          class="governance-directory__filters"
          role="tablist"
          aria-label="Filter students by governance scope"
        >
          <button
            v-for="filter in studentDirectoryFilters"
            :key="filter.value"
            type="button"
            class="governance-directory__filter"
            :class="{ 'governance-directory__filter--active': studentDirectoryFilter === filter.value }"
            :aria-pressed="studentDirectoryFilter === filter.value ? 'true' : 'false'"
            :aria-label="`${filter.label} (${filter.count})`"
            @click="setStudentDirectoryFilter(filter.value)"
          >
            {{ filter.label }}
          </button>
        </div>

        <div v-if="filteredStudentDirectoryRows.length" class="governance-directory__list governance-student-directory__list">
          <article
            v-for="row in filteredStudentDirectoryRows"
            :key="row.key"
            class="governance-directory__item"
          >
            <div class="governance-directory__avatar governance-student-directory__avatar">
              <span class="governance-student-directory__avatar-text">{{ row.initials }}</span>
            </div>

            <div class="governance-directory__info">
              <strong class="governance-directory__name">{{ row.studentName }}</strong>
              <p class="governance-directory__meta">{{ getStudentDirectoryMeta(row) }}</p>
            </div>
          </article>
        </div>

        <article v-else class="governance-empty-card governance-empty-card--subtle">
          <UsersRound :size="18" :stroke-width="2" />
          <div>
            <strong>{{ studentDirectoryEmptyTitle }}</strong>
            <p>{{ studentDirectoryEmptyCopy }}</p>
          </div>
        </article>
      </section>

      <!-- ============================================================ -->
      <!-- GOVERNANCE ADMIN HUB — Apple HIG Inset Grouped List          -->
      <!-- ============================================================ -->
      <section v-else-if="isGovernanceSection" class="gov-admin dashboard-enter dashboard-enter--3">

        <!-- Header -->
        <div class="gov-admin__header">
          <h1 class="gov-admin__title">Governance</h1>
          <p class="gov-admin__subtitle">
            Keep unit structure, officer access, and child-governance ownership aligned to the backend hierarchy.
          </p>
        </div>

        <!-- Group 1: Identity Card -->
        <div class="gov-admin__identity-card">
          <div class="gov-admin__identity-inner">
            <div class="gov-admin__identity-icon">
              <Building2 :size="20" :stroke-width="2" />
            </div>
            <div class="gov-admin__identity-copy">
              <strong class="gov-admin__identity-name">{{ activeUnitName }}</strong>
              <span class="gov-admin__identity-meta">
                Active Unit
                <span v-if="membersCount > 0"> · {{ formatWholeNumber(membersCount) }} {{ membersCount === 1 ? 'Officer' : 'Officers' }}</span>
              </span>
            </div>
            <span class="gov-admin__identity-badge">{{ activeUnitType || 'GOV' }}</span>
          </div>
        </div>

        <div class="gov-admin__guide-card">
          <div class="gov-admin__guide-copy">
            <p class="gov-admin__section-label gov-admin__section-label--flush">Hierarchy Guide</p>
            <h2 class="gov-admin__guide-title">{{ governanceManagedByLabel }}</h2>
            <p class="gov-admin__guide-description">
              {{ governanceGuideDescription }}
            </p>
          </div>

          <div class="gov-admin__guide-rail">
            <article
              v-for="card in governanceHierarchyCards"
              :key="card.key"
              class="gov-admin__guide-step"
              :class="`gov-admin__guide-step--${card.tone}`"
            >
              <span class="gov-admin__guide-step-tag">{{ card.label }}</span>
              <strong class="gov-admin__guide-step-title">{{ card.title }}</strong>
              <p class="gov-admin__guide-step-copy">{{ card.caption }}</p>
            </article>
          </div>

          <div class="gov-admin__guide-pills">
            <span class="gov-admin__guide-pill">Managed by {{ governanceManagedByShortLabel }}</span>
            <span class="gov-admin__guide-pill">{{ governanceManageTargetLabel }}</span>
            <span class="gov-admin__guide-pill gov-admin__guide-pill--muted">Members are assigned from existing students only</span>
          </div>
        </div>

        <!-- Group 2: Org Structure (hidden for ORG tier) -->
        <template v-if="governanceShowChildUnits">
          <p class="gov-admin__section-label">{{ governanceChildUnitsSectionLabel }}</p>
          <div class="gov-admin__group">
            <div class="gov-admin__group-header">
              <span class="gov-admin__group-title">
                {{ activeUnitType === 'SSG' ? 'College Councils' : 'Student Organizations' }}
              </span>
              <button
                v-if="governanceCanAddChildUnit"
                type="button"
                class="gov-admin__add-button"
                aria-label="Create a new child unit"
                @click="handleOpenCreateSheet"
              >
                <Plus :size="14" :stroke-width="2.4" />
                Add
              </button>
            </div>

            <template v-if="governanceChildUnits.length">
              <!-- Each child unit row is a button: clicking navigates to member management
                   for THAT unit — correct per the backend parent-controls-child rule. -->
              <button
                v-for="(unit, index) in governanceChildUnits"
                :key="unit.id || index"
                type="button"
                class="gov-admin__row gov-admin__row--button"
                :class="{ 'gov-admin__row--last': index === governanceChildUnits.length - 1 }"
                :aria-label="`Manage members of ${unit.unit_name || 'this unit'}`"
                @click="navigateToChildUnitMembers(unit)"
              >
                <div class="gov-admin__row-icon">
                  <Building2 :size="16" :stroke-width="2" />
                </div>
                <div class="gov-admin__row-copy">
                  <strong>{{ unit.unit_name || unit.name || 'Unnamed Unit' }}</strong>
                  <span>{{ unit.unit_type || (activeUnitType === 'SSG' ? 'SG' : 'ORG') }}</span>
                </div>
                <div class="gov-admin__row-manage-hint" v-if="governanceCanManageMembers">
                  <span>Manage</span>
                </div>
                <ChevronDown :size="16" :stroke-width="2" class="gov-admin__row-chevron" />
              </button>
            </template>
            <div v-else class="gov-admin__group-empty">
              <span>No {{ activeUnitType === 'SSG' ? 'college councils' : 'organizations' }} assigned yet.</span>
            </div>
          </div>
        </template>

        <!-- Group 3: Unit Officers -->
        <!-- These are the current unit's own officers (e.g. SSG's officers if user is in SSG). -->
        <!-- IMPORTANT: adding to THIS list requires the PARENT to act (campus_admin for SSG,     -->
        <!-- SSG officer for SG). The Add Officer button is intentionally hidden for SSG tier     -->
        <!-- because only campus_admin can assign SSG members. SG/ORG officers see no Add either; -->
        <!-- their parent (SSG/SG) manages them via the child-unit row navigation above.          -->
        <p class="gov-admin__section-label">Unit Officers</p>
        <div class="gov-admin__group">
          <div class="gov-admin__group-header">
            <span class="gov-admin__group-title">Officers &amp; Permissions</span>
          </div>

          <template v-if="governanceOfficerRows.length">
            <button
              v-for="(officer, index) in governanceOfficerRows"
              :key="officer.key"
              type="button"
              class="gov-admin__row gov-admin__row--button"
              :class="{ 'gov-admin__row--last': index === governanceOfficerRows.length - 1 }"
              @click="openOfficerSheet(officer)"
            >
              <div class="gov-admin__avatar">
                <span class="gov-admin__avatar-text">{{ officer.initials }}</span>
              </div>
              <div class="gov-admin__row-copy">
                <strong>{{ officer.name }}</strong>
                <span>{{ officer.role || 'Member' }}</span>
              </div>
              <ChevronDown :size="16" :stroke-width="2" class="gov-admin__row-chevron" />
            </button>
          </template>
          <div v-else class="gov-admin__group-empty">
            <span>No officer records found for this unit.</span>
          </div>
        </div>

        <!-- My Permissions Card -->
        <p class="gov-admin__section-label">My Access</p>
        <div class="gov-admin__group">
          <div class="gov-admin__group-header">
            <span class="gov-admin__group-title">Active Permissions</span>
          </div>
          <template v-if="permissionCodes.length">
            <div
              v-for="(code, index) in permissionCodes"
              :key="code"
              class="gov-admin__row"
              :class="{ 'gov-admin__row--last': index === permissionCodes.length - 1 }"
            >
              <div class="gov-admin__row-icon gov-admin__row-icon--permission">
                <ShieldCheck :size="15" :stroke-width="2.1" />
              </div>
              <div class="gov-admin__row-copy">
                <strong>{{ PERMISSION_LABELS[code] || code.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }}</strong>
                <span>{{ code }}</span>
              </div>
            </div>
          </template>
          <div v-else class="gov-admin__group-empty">
            <span>No permissions have been assigned to your account yet.</span>
          </div>
        </div>

      </section>

      <!-- Officer Permission Bottom Sheet -->
      <Transition name="gov-sheet">
        <div
          v-if="governanceSelectedOfficer"
          class="gov-admin__sheet-backdrop"
          @click.self="closeOfficerSheet"
        >
          <section
            class="gov-admin__sheet"
            role="dialog"
            aria-modal="true"
            :aria-labelledby="'gov-officer-sheet-title'"
          >
            <!-- Sheet Header -->
            <div class="gov-admin__sheet-header">
              <div class="gov-admin__sheet-identity">
                <div class="gov-admin__avatar gov-admin__avatar--large">
                  <span class="gov-admin__avatar-text">{{ governanceSelectedOfficer.initials }}</span>
                </div>
                <div>
                  <h2 id="gov-officer-sheet-title" class="gov-admin__sheet-name">{{ governanceSelectedOfficer.name }}</h2>
                  <p class="gov-admin__sheet-role">{{ governanceSelectedOfficer.role || 'Member' }}</p>
                </div>
              </div>
              <button
                type="button"
                class="gov-admin__sheet-close"
                aria-label="Close permission editor"
                @click="closeOfficerSheet"
              >
                <Plus :size="18" :stroke-width="2.1" style="transform: rotate(45deg);" />
              </button>
            </div>

            <!-- Read-only notice when no assign_permissions -->
            <div v-if="!governanceCanAssignPermissions" class="gov-admin__sheet-notice">
              <ShieldCheck :size="14" :stroke-width="2" />
              <span>Read-only — you need the <strong>assign_permissions</strong> code to edit.</span>
            </div>

            <!-- Permission Toggles -->
            <div class="gov-admin__sheet-toggles">
              <div
                v-for="[code, label] in governancePermissionToggleList"
                :key="code"
                class="gov-admin__permission-row"
              >
                <div class="gov-admin__permission-copy">
                  <strong>{{ label }}</strong>
                  <span>{{ code }}</span>
                </div>
                <button
                  type="button"
                  class="gov-admin__toggle"
                  :class="{ 'gov-admin__toggle--on': governanceSelectedOfficer.permissions.includes(code) }"
                  :disabled="!governanceCanAssignPermissions"
                  :aria-pressed="governanceSelectedOfficer.permissions.includes(code) ? 'true' : 'false'"
                  :aria-label="label"
                  role="switch"
                >
                  <span class="gov-admin__toggle-knob" />
                </button>
              </div>
            </div>
          </section>
        </div>
      </Transition>
    </template>

    <GovernanceCreateSheet
      :open="isCreateSheetOpen"
      :actions="createActions"
      @close="closeCreateSheet"
      @select="handleSheetActionSelect"
    />

    <EventEditorSheet
      :is-open="isEventEditorOpen"
      :event="editingEvent"
      :title="editingEvent ? 'Edit Event' : 'Create Event'"
      :description="editingEvent
        ? 'Update the selected governance event using the live backend event fields.'
        : 'Create a governance-scoped event using the backend event fields.'"
      :submit-label="editingEvent ? 'Save Event' : 'Create Event'"
      :saving="isEventEditorSaving"
      :error-message="eventEditorError"
      @close="closeEventEditor"
      @save="handleEventEditorSave"
    />

    <Transition name="governance-sheet">
      <div
        v-if="isAnnouncementComposerOpen"
        class="governance-sheet__backdrop"
        @click.self="closeAnnouncementComposer"
      >
        <section
          class="governance-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="governance-announcement-composer-title"
        >
          <header class="governance-sheet__header">
            <div class="governance-sheet__copy">
              <p class="governance-sheet__eyebrow">Announcement</p>
              <h2 id="governance-announcement-composer-title" class="governance-sheet__title">
                New Announcement
              </h2>
            </div>

            <button
              type="button"
              class="governance-sheet__close"
              aria-label="Close announcement composer"
              @click="closeAnnouncementComposer"
            >
              <Plus :size="18" :stroke-width="2.1" style="transform: rotate(45deg);" />
            </button>
          </header>

          <form class="governance-sheet__form" @submit.prevent="handleAnnouncementComposerSave">
            <label class="governance-sheet__field">
              <span>Title</span>
              <input
                v-model="announcementDraft.title"
                type="text"
                class="governance-sheet__input"
                placeholder="Announcement title"
              >
            </label>

            <label class="governance-sheet__field">
              <span>Body</span>
              <textarea
                v-model="announcementDraft.body"
                class="governance-sheet__input governance-sheet__input--textarea"
                rows="5"
                placeholder="Share the update for your governance audience."
              />
            </label>

            <label class="governance-sheet__field">
              <span>Status</span>
              <select v-model="announcementDraft.status" class="governance-sheet__input">
                <option value="published">Published</option>
                <option value="draft">Draft</option>
                <option value="archived">Archived</option>
              </select>
            </label>

            <p v-if="announcementComposerError" class="governance-sheet__error">
              {{ announcementComposerError }}
            </p>

            <div class="governance-sheet__actions">
              <button
                type="button"
                class="governance-sheet__secondary"
                :disabled="isAnnouncementComposerSaving"
                @click="closeAnnouncementComposer"
              >
                Cancel
              </button>

              <button
                type="submit"
                class="governance-sheet__primary"
                :disabled="isAnnouncementComposerSaving"
              >
                {{ isAnnouncementComposerSaving ? 'Saving...' : 'Publish' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </Transition>

    <Transition name="governance-sheet">
      <div
        v-if="selectedAnnouncement"
        class="governance-sheet__backdrop"
        @click.self="closeAnnouncementDetail"
      >
        <section
          class="governance-sheet governance-sheet--detail"
          role="dialog"
          aria-modal="true"
          aria-labelledby="governance-announcement-detail-title"
        >
          <header class="governance-sheet__header">
            <div class="governance-sheet__copy">
              <p class="governance-sheet__eyebrow">Announcement</p>
              <h2 id="governance-announcement-detail-title" class="governance-sheet__title">
                {{ selectedAnnouncement.title || 'Untitled announcement' }}
              </h2>
              <p class="governance-sheet__meta">
                {{ formatAnnouncementTime(selectedAnnouncement.created_at || selectedAnnouncement.updated_at) }}
              </p>
            </div>

            <button
              type="button"
              class="governance-sheet__close"
              aria-label="Close announcement detail"
              @click="closeAnnouncementDetail"
            >
              <Plus :size="18" :stroke-width="2.1" style="transform: rotate(45deg);" />
            </button>
          </header>

          <p class="governance-sheet__body">
            {{ selectedAnnouncement.body || 'No announcement body was provided.' }}
          </p>
        </section>
      </div>
    </Transition>

    <Transition name="governance-permission-alert">
      <div
        v-if="isPermissionAlertOpen"
        class="governance-permission-alert__backdrop"
        @click.self="closePermissionAlert"
      >
        <section
          class="governance-permission-alert"
          role="dialog"
          aria-modal="true"
          aria-labelledby="governance-permission-alert-title"
        >
          <div class="governance-permission-alert__icon">
            <AlertCircle :size="20" :stroke-width="2.2" />
          </div>

          <div class="governance-permission-alert__copy">
            <p class="governance-permission-alert__eyebrow">Permission Required</p>
            <h2 id="governance-permission-alert-title" class="governance-permission-alert__title">
              You currently do not have permission for this workspace.
            </h2>
            <p class="governance-permission-alert__description">
              Your account is inside {{ activeUnitName }}, but the backend has not returned any governance
              permission codes yet. Ask your unit administrator to assign access before using management actions.
            </p>
          </div>

          <button
            type="button"
            class="governance-permission-alert__button"
            @click="closePermissionAlert"
          >
            Got it
          </button>
        </section>
      </div>
    </transition>


  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  BellRing,
  Building2,
  CalendarDays,
  ChevronDown,
  CircleAlert,
  Clock3,
  Edit2,
  MoreHorizontal,
  FileSpreadsheet,
  FileText,
  GraduationCap,
  LoaderCircle,
  Megaphone,
  Plus,
  ShieldCheck,
  TrendingUp,
  UsersRound,
  Search,
  Sparkles,
} from 'lucide-vue-next'
import TopBar from '@/components/dashboard/TopBar.vue'
import EventEditorSheet from '@/components/events/EventEditorSheet.vue'
import GovernanceArrivalBars from '@/components/governance/GovernanceArrivalBars.vue'
import GovernanceBreakdownBars from '@/components/governance/GovernanceBreakdownBars.vue'
import GovernanceCreateSheet from '@/components/governance/GovernanceCreateSheet.vue'
import GovernanceProgressRing from '@/components/governance/GovernanceProgressRing.vue'
import GovernanceTrendChart from '@/components/governance/GovernanceTrendChart.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { applyTheme, loadTheme } from '@/config/theme.js'
import {
  createGovernanceAnnouncement,
  createGovernanceEvent,
  getAnnouncements,
  getEvents as getCampusEvents,
  updateEvent as updateBackendEvent,
} from '@/services/backendApi.js'
import { createIdempotencyKey } from '@/services/idempotency.js'
import { useGovernanceWorkspace } from '@/composables/useGovernanceWorkspace.js'
import { useAiDemo } from '@/services/aiDemoHandler.js'
import { normalizeGovernanceContext } from '@/services/governanceScope.js'

const props = defineProps({
  preview: { type: Boolean, default: false },
  section: { type: String, default: 'overview' },
})

const searchQuery = ref('')
const { apiBaseUrl, token } = useDashboardSession()
const router = useRouter()
const { isAiCreating, aiResult } = useAiDemo(searchQuery)

const {
  currentUser,
  schoolSettings,
  permissionCodes,
  activeUnit,
  acronym,
  activeUnitType,
  activeUnitName,
  workspaceEyebrow,
  officerMeta,
  headerTitle,
  headerDescription,
  membersCount,
  students: governanceStudents,
  studentsPreview,
  events,
  upcomingEvents,
  announcements,
  recentAnnouncements,
  permissionBadgeList,
  currentSection,
  isOverviewSection,
  hasRenderableData,
  isWorkspaceLoading,
  workspaceError,
  reportsLoading,
  engagementMetric,
  eventHealthInsight,
  demographicInsight,
  engagementTimeline,
  arrivalInsight,
  analyticsEventOptions,
  attendanceRecordsByEventId,
  selectedAnalyticsEventId,
  activeStudentsMetric,
  totalStudentsMetric,
  eventVolumeMetric,
  latestAnnouncementReachMetric,
  attentionItems,
  exportError,
  isExportingPar,
  isExportingMasterlist,
  analyticsFocusEntry,
  canExportPar,
  canExportMasterlist,
  getEventReportSnapshot,
  isCreateSheetOpen,
  hasPermission,
  openSection,
  openEvent,
  openAttentionItem,
  openCreateSheet,
  closeCreateSheet,
  handleCreateAction,
  setSelectedAnalyticsEventId,
  exportPostActivityReport,
  exportMasterlist,
  exportEventPostActivityReport,
  exportEventMasterlist,
  getUpcomingEventActionLabel,
  getUpcomingEventTone,
  formatStudentName,
  formatStudentMeta,
  formatEventLine,
  formatDateRange,
  formatAnnouncementTime,
  formatWholeNumber,
  getStatusLabel,
} = useGovernanceWorkspace({
  preview: props.preview,
  section: () => props.section,
})

const searchActive = computed(() => searchQuery.value.trim().length > 0)
const hasGovernancePermissionCodes = computed(() => permissionCodes.value.length > 0)
const isPermissionAlertOpen = ref(false)
const hasShownPermissionAlert = ref(false)
const isEnhancedOverview = computed(() => isOverviewSection.value && Boolean(activeUnitType.value))
const isEventsSection = computed(() => currentSection.value.key === 'events')
const isStudentsSection = computed(() => currentSection.value.key === 'students')
const isGovernanceSection = computed(() => currentSection.value.key === 'governance')
const showWorkspaceTopRow = computed(() => isOverviewSection.value)
const showGovernanceTopBar = computed(() => !selectedEventForAttendance.value)
const eventFeedMode = ref('council')
const campusEvents = ref([])
const campusAnnouncements = ref([])
const isCampusFeedLoading = ref(false)
const campusFeedError = ref('')
const selectedAnnouncement = ref(null)
const isAnnouncementComposerOpen = ref(false)
const isAnnouncementComposerSaving = ref(false)
const announcementComposerError = ref('')
const announcementDraft = ref(createAnnouncementDraft())
const isEventEditorOpen = ref(false)
const isEventEditorSaving = ref(false)
const eventEditorError = ref('')
const pendingEventCreateRequestKey = ref('')
const editingEvent = ref(null)
const eventListFilter = ref('all')
const expandedEventId = ref(null)
const selectedEventForAttendance = ref(null)
const attendanceDirectoryFilter = ref('all')
const studentDirectoryQuery = ref('')
const studentDirectoryFilter = ref('all')

function openAttendanceSheet(event) {
  if (!event) return
  selectedEventForAttendance.value = event
  attendanceDirectoryFilter.value = 'all'
}

function closeAttendanceSheet() {
  selectedEventForAttendance.value = null
  attendanceDirectoryFilter.value = 'all'
}

const calendarMonthCursor = ref(startOfMonth(new Date()))
const selectedCalendarDateKey = ref('')
const eventSwipeOffsets = ref({})
const eventSwipeDragId = ref(null)
const eventSwipePointerId = ref(null)
const eventSwipeStartX = ref(0)
const eventSwipeStartY = ref(0)
const eventSwipeStartOffset = ref(0)
const eventSwipeAxisLock = ref(null)
const eventSwipeDidDrag = ref(false)

const EVENT_SWIPE_ACTION_WIDTH = 110
const EVENT_SWIPE_OPEN_THRESHOLD = 42
const EVENT_SWIPE_GESTURE_THRESHOLD = 8

function createAnnouncementDraft() {
  return {
    title: '',
    body: '',
    status: 'published',
  }
}

function toTimestamp(value) {
  const timestamp = value ? new Date(value).getTime() : Number.NaN
  return Number.isFinite(timestamp) ? timestamp : null
}

function resolveEventFeedState(event = null) {
  const status = String(event?.status || '').trim().toLowerCase()
  if (status === 'ongoing' || status === 'active') return 'ongoing'
  if (['completed', 'done', 'closed', 'ended', 'archived'].includes(status)) return 'done'
  if (['upcoming', 'scheduled', 'draft', 'published'].includes(status)) return 'upcoming'

  const now = Date.now()
  const start = toTimestamp(event?.start_datetime || event?.start_time)
  const end = toTimestamp(event?.end_datetime || event?.end_time)
  if (start != null && end != null && now >= start && now <= end) return 'ongoing'
  if (end != null && now > end) return 'done'
  return 'upcoming'
}

function isLiveEventRecord(event = null) {
  return resolveEventFeedState(event) === 'ongoing'
}

function sortEventFeed(values = []) {
  const statusRank = {
    ongoing: 0,
    upcoming: 1,
    done: 2,
  }

  return [...values].sort((left, right) => {
    const leftRank = statusRank[resolveEventFeedState(left)] ?? 99
    const rightRank = statusRank[resolveEventFeedState(right)] ?? 99
    if (leftRank !== rightRank) return leftRank - rightRank

    return (toTimestamp(left?.start_datetime || left?.start_time) || 0)
      - (toTimestamp(right?.start_datetime || right?.start_time) || 0)
  })
}

function getEventFeedStateLabel(event = null) {
  const state = resolveEventFeedState(event)
  if (state === 'ongoing') return 'Ongoing'
  if (state === 'done') return 'Done'
  return 'Upcoming'
}

function sortAnnouncementFeed(values = []) {
  return [...values].sort((left, right) => {
    return (toTimestamp(right?.created_at || right?.updated_at) || 0)
      - (toTimestamp(left?.created_at || left?.updated_at) || 0)
  })
}

const monthFormatter = new Intl.DateTimeFormat('en-US', { month: 'short' })
const dayFormatter = new Intl.DateTimeFormat('en-US', { day: '2-digit' })
const compactTimeFormatter = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' })
const calendarMonthFormatter = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' })
const calendarDayTitleFormatter = new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric' })
const calendarWeekdayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function formatEventMonth(event = null) {
  const value = event?.start_datetime || event?.start_time
  if (!value) return 'TBD'
  try {
    return monthFormatter.format(new Date(value)).toUpperCase()
  } catch {
    return 'TBD'
  }
}

function formatEventDay(event = null) {
  const value = event?.start_datetime || event?.start_time
  if (!value) return '--'
  try {
    return dayFormatter.format(new Date(value))
  } catch {
    return '--'
  }
}

function formatEventRangeCompact(event = null) {
  const startValue = event?.start_datetime || event?.start_time
  const endValue = event?.end_datetime || event?.end_time

  if (!startValue) return 'Schedule pending'

  try {
    const startLabel = compactTimeFormatter.format(new Date(startValue))
    if (!endValue) return startLabel
    return `${startLabel} - ${compactTimeFormatter.format(new Date(endValue))}`
  } catch {
    return 'Schedule pending'
  }
}

function startOfMonth(date = new Date()) {
  const nextDate = new Date(date)
  nextDate.setDate(1)
  nextDate.setHours(0, 0, 0, 0)
  return nextDate
}

function addMonths(date = new Date(), amount = 0) {
  const nextDate = new Date(date)
  nextDate.setMonth(nextDate.getMonth() + amount)
  return startOfMonth(nextDate)
}

function getDateKey(value = null) {
  const parsed = value ? new Date(value) : null
  if (!parsed || Number.isNaN(parsed.getTime())) return ''
  return `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, '0')}-${String(parsed.getDate()).padStart(2, '0')}`
}

function normalizeScopeIdList(values = []) {
  return [...new Set(
    (Array.isArray(values) ? values : [values])
      .map((value) => Number(value))
      .filter(Number.isFinite)
  )]
}

function resolveGovernanceStudentUser(student = null) {
  return student?.user || student || null
}

function resolveGovernanceStudentProfile(student = null) {
  const directProfile = student?.student_profile
  if (directProfile && typeof directProfile === 'object') return directProfile

  const nestedProfile = student?.user?.student_profile
  return nestedProfile && typeof nestedProfile === 'object' ? nestedProfile : {}
}

function resolveGovernanceStudentName(student = null) {
  const user = resolveGovernanceStudentUser(student)
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim()
    || user?.email
    || 'Unknown Student'
}

function resolveGovernanceStudentIdentifier(student = null, record = null) {
  const user = resolveGovernanceStudentUser(student)
  const profile = resolveGovernanceStudentProfile(student)

  return [
    record?.student_id,
    student?.student_id,
    profile?.student_id,
    user?.student_id,
  ]
    .map((value) => String(value || '').trim())
    .find(Boolean)
    || 'Student record'
}

function resolveGovernanceStudentDepartmentName(student = null, record = null) {
  const user = resolveGovernanceStudentUser(student)
  const profile = resolveGovernanceStudentProfile(student)

  return [
    record?.department_name,
    record?.student_department_name,
    student?.department_name,
    profile?.department_name,
    user?.department_name,
  ]
    .map((value) => String(value || '').trim())
    .find(Boolean)
    || ''
}

function resolveGovernanceStudentProgramName(student = null, record = null) {
  const user = resolveGovernanceStudentUser(student)
  const profile = resolveGovernanceStudentProfile(student)

  return [
    record?.program_name,
    record?.student_program_name,
    student?.program_name,
    profile?.program_name,
    user?.program_name,
  ]
    .map((value) => String(value || '').trim())
    .find(Boolean)
    || ''
}

function buildStudentDirectoryInitials(name = '') {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'ST'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
}

function resolveStudentDirectoryMode() {
  if (activeUnitType.value === 'SSG') return 'college'
  if (activeUnitType.value === 'SG') return 'program'
  return 'direct'
}

function buildStudentDirectoryRow(student = null) {
  const user = resolveGovernanceStudentUser(student)
  const profile = resolveGovernanceStudentProfile(student)
  const studentName = resolveGovernanceStudentName(student)
  const studentId = resolveGovernanceStudentIdentifier(student)
  const rawDepartmentName = resolveGovernanceStudentDepartmentName(student)
  const rawProgramName = resolveGovernanceStudentProgramName(student)
  const yearLevel = Number(profile?.year_level)
  const yearLabel = Number.isFinite(yearLevel) && yearLevel > 0 ? `Year ${yearLevel}` : ''

  return {
    key: [
      Number(profile?.id),
      Number(user?.id),
      studentId,
      studentName.toLowerCase(),
    ].find((value) => value != null && String(value).trim() !== ''),
    studentName,
    studentId,
    email: String(user?.email || '').trim(),
    rawDepartmentName,
    rawProgramName,
    departmentName: rawDepartmentName || 'Unassigned College',
    programName: rawProgramName || 'Unassigned Program',
    yearLabel,
    initials: buildStudentDirectoryInitials(studentName),
  }
}

const studentDirectoryRows = computed(() => (
  governanceStudents.value
    .map((student) => buildStudentDirectoryRow(student))
    .sort((left, right) => left.studentName.localeCompare(right.studentName))
))

const studentDirectoryMode = computed(() => {
  const requestedMode = resolveStudentDirectoryMode()

  if (requestedMode === 'college') {
    return studentDirectoryRows.value.some((row) => row.rawDepartmentName) ? 'college' : 'direct'
  }

  if (requestedMode === 'program') {
    return studentDirectoryRows.value.some((row) => row.rawProgramName) ? 'program' : 'direct'
  }

  return 'direct'
})

const studentDirectoryFilters = computed(() => {
  if (studentDirectoryMode.value === 'direct') return []

  const counts = new Map()
  const targetKey = studentDirectoryMode.value === 'college' ? 'rawDepartmentName' : 'rawProgramName'

  studentDirectoryRows.value.forEach((row) => {
    const label = String(row?.[targetKey] || '').trim()
    if (!label) return
    counts.set(label, (counts.get(label) || 0) + 1)
  })

  return [
    {
      value: 'all',
      label: 'All',
      count: studentDirectoryRows.value.length,
    },
    ...Array.from(counts.entries())
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([label, count]) => ({
        value: label,
        label,
        count,
      })),
  ]
})

const filteredStudentDirectoryRows = computed(() => {
  const normalizedQuery = studentDirectoryQuery.value.trim().toLowerCase()

  return studentDirectoryRows.value.filter((row) => {
    if (studentDirectoryMode.value !== 'direct' && studentDirectoryFilter.value !== 'all') {
      const label = studentDirectoryMode.value === 'college' ? row.rawDepartmentName : row.rawProgramName
      if (String(label || '').trim() !== studentDirectoryFilter.value) {
        return false
      }
    }

    if (!normalizedQuery) return true

    const searchHaystack = [
      row.studentName,
      row.studentId,
      row.email,
      row.rawDepartmentName,
      row.rawProgramName,
      row.yearLabel,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return searchHaystack.includes(normalizedQuery)
  })
})

const studentDirectorySearchPlaceholder = computed(() => {
  if (studentDirectoryMode.value === 'college') return 'Search students, IDs, or colleges'
  if (studentDirectoryMode.value === 'program') return 'Search students, IDs, or programs'
  return 'Search students or IDs'
})

const studentDirectoryEmptyTitle = computed(() => (
  studentDirectoryRows.value.length
    ? 'No students match this view.'
    : 'No students are currently exposed in this governance scope.'
))

const studentDirectoryEmptyCopy = computed(() => (
  studentDirectoryRows.value.length
    ? 'Try clearing the search or choosing a different scope filter.'
    : 'The backend did not return any students for the active governance unit.'
))

function getStudentDirectoryMeta(row = null) {
  const parts = [String(row?.studentId || '').trim()]

  if (studentDirectoryMode.value === 'college' && row?.departmentName) {
    parts.push(row.departmentName)
  } else if (studentDirectoryMode.value === 'program' && row?.programName) {
    parts.push(row.programName)
  } else {
    if (row?.yearLabel) parts.push(row.yearLabel)
    else if (row?.programName) parts.push(row.programName)
    else if (row?.departmentName) parts.push(row.departmentName)
  }

  return parts.filter(Boolean).join(' • ')
}

function resolveAttendanceDirectoryStudentKeys(student = null) {
  const user = resolveGovernanceStudentUser(student)
  const profile = resolveGovernanceStudentProfile(student)
  const keys = []

  if (Number.isFinite(Number(user?.id))) {
    keys.push(`user:${Number(user.id)}`)
  }

  if (Number.isFinite(Number(profile?.id))) {
    keys.push(`profile:${Number(profile.id)}`)
  }

  const studentId = resolveGovernanceStudentIdentifier(student)
  if (studentId && studentId !== 'Student record') {
    keys.push(`student:${studentId.toLowerCase()}`)
  }

  const fullName = resolveGovernanceStudentName(student).trim().toLowerCase()
  if (fullName && fullName !== 'unknown student') {
    keys.push(`name:${fullName}`)
  }

  return [...new Set(keys)]
}

function buildGovernanceStudentLookup(students = []) {
  const lookup = new Map()

  ;(Array.isArray(students) ? students : []).forEach((student) => {
    resolveAttendanceDirectoryStudentKeys(student).forEach((key) => {
      if (!lookup.has(key)) lookup.set(key, student)
    })
  })

  return lookup
}

function resolveAttendanceDirectoryRecordKey(record = null) {
  const attendance = record?.attendance || {}
  const numericProfileId = Number(attendance?.student_id)
  if (Number.isFinite(numericProfileId)) return `profile:${numericProfileId}`

  const studentId = String(record?.student_id || '').trim().toLowerCase()
  if (studentId) return `student:${studentId}`

  const studentName = String(record?.student_name || '').trim().toLowerCase()
  if (studentName) return `name:${studentName}`

  return `row:${String(attendance?.id || '').trim() || 'unknown'}`
}

function resolveMatchedGovernanceStudent(record = null, lookup = new Map()) {
  const attendance = record?.attendance || {}
  const keys = []

  const numericProfileId = Number(attendance?.student_id)
  if (Number.isFinite(numericProfileId)) {
    keys.push(`profile:${numericProfileId}`)
  }

  const studentId = String(record?.student_id || '').trim().toLowerCase()
  if (studentId) {
    keys.push(`student:${studentId}`)
  }

  const studentName = String(record?.student_name || '').trim().toLowerCase()
  if (studentName) {
    keys.push(`name:${studentName}`)
  }

  for (const key of keys) {
    if (lookup.has(key)) return lookup.get(key)
  }

  return null
}

function getAttendanceDirectoryRecordTimestamp(record = null) {
  const attendance = record?.attendance || {}
  const timestamp = new Date(
    attendance?.time_out
    || attendance?.time_in
    || record?.created_at
    || 0
  ).getTime()

  return Number.isFinite(timestamp) ? timestamp : 0
}

function dedupeAttendanceDirectoryRecords(records = []) {
  const latestByStudent = new Map()

  for (const record of Array.isArray(records) ? records : []) {
    const key = resolveAttendanceDirectoryRecordKey(record)
    const existing = latestByStudent.get(key)
    if (!existing || getAttendanceDirectoryRecordTimestamp(record) >= getAttendanceDirectoryRecordTimestamp(existing)) {
      latestByStudent.set(key, record)
    }
  }

  return Array.from(latestByStudent.values())
}

function studentMatchesSelectedEventScope(student = null, event = null) {
  if (!student || !event) return false

  const profile = resolveGovernanceStudentProfile(student)
  const departmentIds = normalizeScopeIdList(event?.department_ids)
  const programIds = normalizeScopeIdList(event?.program_ids)
  const studentDepartmentId = Number(profile?.department_id)
  const studentProgramId = Number(profile?.program_id)

  if (programIds.length > 0) {
    return Number.isFinite(studentProgramId) && programIds.includes(studentProgramId)
  }

  if (departmentIds.length > 0) {
    return Number.isFinite(studentDepartmentId) && departmentIds.includes(studentDepartmentId)
  }

  return true
}

function resolveAttendanceDirectoryMode(event = null) {
  const programIds = normalizeScopeIdList(event?.program_ids)
  if (programIds.length > 0) return 'direct'
  if (activeUnitType.value === 'SSG') return 'college'
  if (activeUnitType.value === 'SG') return 'program'
  return 'direct'
}

function formatAttendanceStatusFallback(value = '') {
  return String(value || '')
    .trim()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function resolveAttendanceDirectoryStatusCategory(attendance = null, event = null) {
  const normalizedDisplayStatus = String(
    attendance?.display_status
    || attendance?.check_out_status
    || attendance?.check_in_status
    || attendance?.status
    || ''
  ).trim().toLowerCase()
  const completionState = String(attendance?.completion_state || '').trim().toLowerCase()

  if (!attendance || typeof attendance !== 'object' || Object.keys(attendance).length === 0) {
    return resolveEventFeedState(event) === 'done' ? 'absent' : 'neutral'
  }

  const eventIsFinal = resolveEventFeedState(event) === 'done'
  const signedInWithoutSignOut = Boolean(attendance?.time_in && !attendance?.time_out)

  if (eventIsFinal && signedInWithoutSignOut) {
    return 'absent'
  }

  if (
    completionState === 'incomplete'
    || normalizedDisplayStatus === 'incomplete'
    || normalizedDisplayStatus === 'waiting'
    || normalizedDisplayStatus === 'waiting_for_sign_out'
    || signedInWithoutSignOut
  ) {
    return 'waiting'
  }

  if (normalizedDisplayStatus === 'late') return 'late'
  if (normalizedDisplayStatus === 'absent') return 'absent'
  if (normalizedDisplayStatus === 'excused') return 'excused'
  if (normalizedDisplayStatus === 'present') return 'present'
  if (attendance?.time_in || attendance?.time_out) return 'present'

  return resolveEventFeedState(event) === 'done' ? 'absent' : 'neutral'
}

function resolveAttendanceDirectoryStatusLabel(attendance = null, event = null, category = null) {
  const resolvedCategory = category || resolveAttendanceDirectoryStatusCategory(attendance, event)
  if (resolvedCategory === 'waiting') return 'Waiting for Sign Out'
  if (resolvedCategory === 'late') return 'Late'
  if (resolvedCategory === 'absent') return 'Absent'
  if (resolvedCategory === 'excused') return 'Excused'
  if (resolvedCategory === 'present') return 'Present'

  const rawStatus = formatAttendanceStatusFallback(
    attendance?.display_status
    || attendance?.check_out_status
    || attendance?.check_in_status
    || attendance?.status
  )

  return rawStatus || 'Not Marked'
}

const selectedEventScopeStudents = computed(() => {
  const event = selectedEventForAttendance.value
  if (!event) return []

  return governanceStudents.value.filter((student) => studentMatchesSelectedEventScope(student, event))
})

const attendanceDirectoryMode = computed(() => {
  const requestedMode = resolveAttendanceDirectoryMode(selectedEventForAttendance.value)

  if (requestedMode === 'college') {
    const hasCollegeMetadata = selectedEventScopeStudents.value.some((student) =>
      Boolean(resolveGovernanceStudentDepartmentName(student))
    )
    return hasCollegeMetadata ? 'college' : 'direct'
  }

  if (requestedMode === 'program') {
    const hasProgramMetadata = selectedEventScopeStudents.value.some((student) =>
      Boolean(resolveGovernanceStudentProgramName(student))
    )
    return hasProgramMetadata ? 'program' : 'direct'
  }

  return 'direct'
})

const attendanceDirectoryFilters = computed(() => {
  if (!selectedEventForAttendance.value || attendanceDirectoryMode.value === 'direct') return []

  const counts = new Map()
  const resolveFilterLabel = attendanceDirectoryMode.value === 'college'
    ? resolveGovernanceStudentDepartmentName
    : resolveGovernanceStudentProgramName

  selectedEventScopeStudents.value.forEach((student) => {
    const label = resolveFilterLabel(student)
    if (!label) return
    counts.set(label, (counts.get(label) || 0) + 1)
  })

  return [
    {
      value: 'all',
      label: 'All',
      count: selectedEventScopeStudents.value.length,
    },
    ...Array.from(counts.entries())
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([label, count]) => ({
        value: label,
        label,
        count,
      })),
  ]
})

function getEventAudienceLabel(event = null, mode = eventFeedMode.value) {
  const explicitLabel = String(
    event?.audience_label
    || event?.scope_label
    || event?.target_label
    || ''
  ).trim()
  if (explicitLabel) return explicitLabel

  const departmentIds = normalizeScopeIdList(event?.department_ids)
  const programIds = normalizeScopeIdList(event?.program_ids)

  if (programIds.length > 0) return programIds.length > 1 ? 'Programs' : 'Program'
  if (departmentIds.length > 0) return departmentIds.length > 1 ? 'Colleges' : 'College'
  if (mode === 'campus') return 'Campus'
  if (activeUnitType.value === 'SSG') return 'All Students'
  if (activeUnitType.value === 'SG') return 'College Scope'
  if (activeUnitType.value === 'ORG') return 'Organization'
  return 'General'
}

const selectedFeedEvents = computed(() => {
  const source = eventFeedMode.value === 'campus' ? campusEvents.value : events.value
  return sortEventFeed(source)
})

const eventFeedFilters = computed(() => {
  const items = selectedFeedEvents.value
  const countByState = items.reduce((accumulator, event) => {
    const state = resolveEventFeedState(event)
    accumulator[state] = (accumulator[state] || 0) + 1
    return accumulator
  }, { ongoing: 0, upcoming: 0, done: 0 })

  return [
    {
      value: 'all',
      label: 'All',
      count: items.length,
    },
    {
      value: 'ongoing',
      label: 'Ongoing',
      count: countByState.ongoing,
    },
    {
      value: 'upcoming',
      label: 'Upcoming',
      count: countByState.upcoming,
    },
    {
      value: 'done',
      label: 'Done',
      count: countByState.done,
    },
  ]
})

const filteredEventFeedList = computed(() => {
  if (eventListFilter.value === 'all') return selectedFeedEvents.value
  return selectedFeedEvents.value.filter((event) => resolveEventFeedState(event) === eventListFilter.value)
})

const calendarEventCountByDate = computed(() => (
  filteredEventFeedList.value.reduce((accumulator, event) => {
    const dateKey = getDateKey(event?.start_datetime || event?.start_time)
    if (!dateKey) return accumulator
    accumulator[dateKey] = (accumulator[dateKey] || 0) + 1
    return accumulator
  }, {})
))

const calendarMonthLabel = computed(() => calendarMonthFormatter.format(calendarMonthCursor.value))

const calendarDays = computed(() => {
  const currentMonthStart = startOfMonth(calendarMonthCursor.value)
  const gridStart = new Date(currentMonthStart)
  gridStart.setDate(gridStart.getDate() - gridStart.getDay())
  const todayKey = getDateKey(new Date())
  const monthIndex = currentMonthStart.getMonth()

  return Array.from({ length: 42 }, (_, index) => {
    const dayDate = new Date(gridStart)
    dayDate.setDate(gridStart.getDate() + index)
    const dateKey = getDateKey(dayDate)

    return {
      key: `${dateKey}-${index}`,
      date: dayDate,
      dateKey,
      dayNumber: dayDate.getDate(),
      isCurrentMonth: dayDate.getMonth() === monthIndex,
      isToday: dateKey === todayKey,
      isSelected: dateKey === selectedCalendarDateKey.value,
      eventCount: calendarEventCountByDate.value[dateKey] || 0,
    }
  })
})

const calendarMonthScopedEvents = computed(() => {
  const monthStart = startOfMonth(calendarMonthCursor.value)
  const nextMonthStart = addMonths(monthStart, 1)
  return filteredEventFeedList.value.filter((event) => {
    const startValue = event?.start_datetime || event?.start_time
    const timestamp = toTimestamp(startValue)
    return timestamp != null && timestamp >= monthStart.getTime() && timestamp < nextMonthStart.getTime()
  })
})

const calendarEventFeedList = computed(() => {
  if (!selectedCalendarDateKey.value) return calendarMonthScopedEvents.value
  return calendarMonthScopedEvents.value.filter((event) => (
    getDateKey(event?.start_datetime || event?.start_time) === selectedCalendarDateKey.value
  ))
})

const eventListTitle = computed(() => (
  selectedCalendarDateKey.value
    ? calendarDayTitleFormatter.format(new Date(selectedCalendarDateKey.value))
    : `${calendarMonthLabel.value} Events`
))

const eventFeedModeLabel = computed(() => (
  eventFeedMode.value === 'campus' ? 'Campus' : 'Council'
))

const isActiveEventsFeedLoading = computed(() => (
  eventFeedMode.value === 'campus' && isCampusFeedLoading.value
))

const activeEventsFeedError = computed(() => (
  eventFeedMode.value === 'campus' ? campusFeedError.value : workspaceError.value
))

const canSwipeEditEvents = computed(() => (
  eventFeedMode.value === 'council' && hasPermission('manage_events')
))

const hasOpenEventSwipe = computed(() => (
  Object.values(eventSwipeOffsets.value).some((offset) => offset > 0)
))

function setEventFeedMode(mode = 'council') {
  eventFeedMode.value = mode === 'campus' ? 'campus' : 'council'
}

function setEventListFilter(mode = 'all') {
  eventListFilter.value = ['ongoing', 'upcoming', 'done'].includes(mode) ? mode : 'all'
}

function setAttendanceDirectoryFilter(value = 'all') {
  const normalizedValue = String(value || 'all').trim()
  attendanceDirectoryFilter.value = normalizedValue || 'all'
}

function setStudentDirectoryFilter(value = 'all') {
  const normalizedValue = String(value || 'all').trim()
  studentDirectoryFilter.value = normalizedValue || 'all'
}

function shiftCalendarMonth(amount = 0) {
  calendarMonthCursor.value = addMonths(calendarMonthCursor.value, amount)
  selectedCalendarDateKey.value = ''
}


function isEventExpanded(eventId) {
  return Number(expandedEventId.value) === Number(eventId)
}

function toggleEventExpanded(eventId) {
  const normalizedId = Number(eventId)
  if (!Number.isFinite(normalizedId)) return
  expandedEventId.value = Number(expandedEventId.value) === normalizedId ? null : normalizedId
}

function selectCalendarDay(day = null) {
  if (!day?.date) return
  if (!day.isCurrentMonth) {
    calendarMonthCursor.value = startOfMonth(day.date)
  }

  selectedCalendarDateKey.value = selectedCalendarDateKey.value === day.dateKey ? '' : day.dateKey
}



function getEventCardSnapshot(event = null) {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) {
    return {
      checkedInLabel: '0',
      checkedOutLabel: '0',
      canExportPar: false,
      canExportMasterlist: false,
    }
  }

  return getEventReportSnapshot(event)
}

function buildAttendanceDirectoryRow({ student = null, record = null, event = null, lookup = new Map() } = {}) {
  const matchedStudent = student || resolveMatchedGovernanceStudent(record, lookup)
  const attendance = record?.attendance || null
  const rowIdentity = record
    ? resolveAttendanceDirectoryRecordKey(record)
    : resolveAttendanceDirectoryStudentKeys(matchedStudent)[0]
      || `student:${resolveGovernanceStudentIdentifier(matchedStudent, record).toLowerCase()}`
  const statusCategory = resolveAttendanceDirectoryStatusCategory(attendance, event)

  return {
    key: `${rowIdentity}:${attendance?.id ?? 'base'}`,
    studentId: resolveGovernanceStudentIdentifier(matchedStudent, record),
    studentName: String(record?.student_name || resolveGovernanceStudentName(matchedStudent)).trim() || 'Unknown Student',
    departmentName: resolveGovernanceStudentDepartmentName(matchedStudent, record) || 'Unassigned College',
    programName: resolveGovernanceStudentProgramName(matchedStudent, record) || 'Unassigned Program',
    statusCategory,
    statusLabel: resolveAttendanceDirectoryStatusLabel(attendance, event, statusCategory),
  }
}

const selectedEventAttendanceRows = computed(() => {
  const event = selectedEventForAttendance.value
  const normalizedEventId = Number(event?.id)
  if (!event || !Number.isFinite(normalizedEventId)) return []

  const scopedStudents = selectedEventScopeStudents.value
  const records = dedupeAttendanceDirectoryRecords(attendanceRecordsByEventId.value?.[normalizedEventId] || [])
  const lookup = buildGovernanceStudentLookup(scopedStudents.length ? scopedStudents : governanceStudents.value)
  const recordByKey = new Map(records.map((record) => [resolveAttendanceDirectoryRecordKey(record), record]))
  const usedRecordKeys = new Set()
  const rows = []

  scopedStudents.forEach((student) => {
    let matchedRecord = null

    for (const key of resolveAttendanceDirectoryStudentKeys(student)) {
      if (recordByKey.has(key)) {
        matchedRecord = recordByKey.get(key)
        usedRecordKeys.add(key)
        break
      }
    }

    rows.push(buildAttendanceDirectoryRow({
      student,
      record: matchedRecord,
      event,
      lookup,
    }))
  })

  records.forEach((record) => {
    const key = resolveAttendanceDirectoryRecordKey(record)
    if (usedRecordKeys.has(key)) return

    rows.push(buildAttendanceDirectoryRow({
      record,
      event,
      lookup,
    }))
  })

  return rows
    .filter((row) => {
      if (attendanceDirectoryMode.value === 'direct' || attendanceDirectoryFilter.value === 'all') {
        return true
      }

      const targetLabel = attendanceDirectoryMode.value === 'college'
        ? row.departmentName
        : row.programName

      return String(targetLabel || '').trim() === attendanceDirectoryFilter.value
    })
    .sort((left, right) => left.studentName.localeCompare(right.studentName))
})

function getAttendanceDirectoryMeta(row = null) {
  const parts = [String(row?.studentId || '').trim()]

  if (attendanceDirectoryMode.value === 'college' && row?.departmentName) {
    parts.push(row.departmentName)
  } else if (attendanceDirectoryMode.value === 'program' && row?.programName) {
    parts.push(row.programName)
  } else if (row?.programName) {
    parts.push(row.programName)
  } else if (row?.departmentName) {
    parts.push(row.departmentName)
  }

  return parts.filter(Boolean).join(' • ')
}

function handleExportEventPar(event = null) {
  exportEventPostActivityReport(event)
}

function handleExportEventCsv(event = null) {
  exportEventMasterlist(event)
}

async function loadCampusFeed() {
  if (!isEventsSection.value || eventFeedMode.value !== 'campus') return

  if (props.preview) {
    campusEvents.value = sortEventFeed(events.value.map((event) => ({ ...event })))
    campusAnnouncements.value = sortAnnouncementFeed(announcements.value.map((announcement) => ({ ...announcement })))
    campusFeedError.value = ''
    return
  }

  if (!apiBaseUrl.value || !token.value) {
    campusFeedError.value = 'Campus events are unavailable right now.'
    return
  }

  isCampusFeedLoading.value = true
  campusFeedError.value = ''

  try {
    const [nextEvents, nextAnnouncements] = await Promise.all([
      getCampusEvents(apiBaseUrl.value, token.value, { limit: 200 }),
      getAnnouncements(apiBaseUrl.value, token.value, { limit: 20 }),
    ])

    campusEvents.value = sortEventFeed(nextEvents)
    campusAnnouncements.value = sortAnnouncementFeed(nextAnnouncements)
  } catch (error) {
    campusFeedError.value = error?.message || 'Unable to load the campus event feed.'
  } finally {
    isCampusFeedLoading.value = false
  }
}

watch(
  [isEventsSection, eventFeedMode, apiBaseUrl, token],
  ([nextIsEventsSection, nextMode]) => {
    if (nextIsEventsSection && nextMode === 'campus') {
      loadCampusFeed()
    }
  },
  { immediate: true }
)

const searchResults = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []

  const results = []

  studentsPreview.value.forEach(student => {
    const name = formatStudentName(student)
    const meta = formatStudentMeta(student)
    if (name.toLowerCase().includes(query) || meta.toLowerCase().includes(query)) {
      results.push({
        id: `student-${student.id || student.user_id}`,
        type: 'student',
        label: name,
        sublabel: meta,
        icon: UsersRound,
        data: student
      })
    }
  })

  events.value.forEach(event => {
    const name = event.name || 'Untitled event'
    const loc = event.location || ''
    if (name.toLowerCase().includes(query) || loc.toLowerCase().includes(query)) {
      results.push({
        id: `event-${event.id}`,
        type: 'event',
        label: name,
        sublabel: formatEventLine(event),
        icon: CalendarDays,
        data: event
      })
    }
  })

  announcements.value.forEach(ann => {
    const title = ann.title || 'Untitled announcement'
    if (title.toLowerCase().includes(query)) {
      results.push({
        id: `ann-${ann.id}`,
        type: 'announcement',
        label: title,
        sublabel: formatAnnouncementTime(ann.created_at || ann.updated_at),
        icon: BellRing,
        data: ann
      })
    }
  })

  return results.slice(0, 6)
})

function handleSearchResultClick(item) {
  if (item.type === 'event') {
    openEvent(item.data)
  } else if (item.type === 'student') {
    openSection('students')
  } else if (item.type === 'announcement') {
    openSection('events')
  }
  searchQuery.value = ''
}

function closePermissionAlert() {
  isPermissionAlertOpen.value = false
}

function handleOpenCreateSheet() {
  if (isWorkspaceLoading.value) return

  if (!activeUnitType.value) {
    openCreateSheet()
    return
  }

  if (!hasGovernancePermissionCodes.value) {
    isPermissionAlertOpen.value = true
    hasShownPermissionAlert.value = true
    return
  }

  openCreateSheet()
}

watch(
  [() => props.preview, schoolSettings],
  ([preview, nextSchoolSettings]) => {
    if (!preview || !nextSchoolSettings) return
    applyTheme(loadTheme(nextSchoolSettings))
  },
  { immediate: true }
)

watch(selectedAnalyticsEventId, () => {
  closeReportMenu()
})

watch([eventFeedMode, eventListFilter], () => {
  closeAllGovernanceEventSwipes()
  expandedEventId.value = null
  selectedCalendarDateKey.value = ''
})

watch(calendarEventFeedList, (nextEvents) => {
  const expandedId = Number(expandedEventId.value)
  if (!Number.isFinite(expandedId)) return
  const stillVisible = nextEvents.some((event) => Number(event?.id) === expandedId)
  if (!stillVisible) {
    expandedEventId.value = null
  }
})

watch(selectedFeedEvents, (nextEvents) => {
  if (!nextEvents.length) {
    calendarMonthCursor.value = startOfMonth(new Date())
    selectedCalendarDateKey.value = ''
    return
  }

  const hasEventsInVisibleMonth = nextEvents.some((event) => {
    const value = event?.start_datetime || event?.start_time
    const timestamp = toTimestamp(value)
    if (timestamp == null) return false

    const monthStart = startOfMonth(calendarMonthCursor.value).getTime()
    const nextMonth = addMonths(calendarMonthCursor.value, 1).getTime()
    return timestamp >= monthStart && timestamp < nextMonth
  })

  if (!hasEventsInVisibleMonth) {
    const firstEventDate = nextEvents[0]?.start_datetime || nextEvents[0]?.start_time
    if (firstEventDate) {
      calendarMonthCursor.value = startOfMonth(new Date(firstEventDate))
    }
  }
}, { immediate: true })

watch(isStudentsSection, (nextValue) => {
  if (!nextValue) {
    studentDirectoryQuery.value = ''
    studentDirectoryFilter.value = 'all'
  }
})

watch(studentDirectoryFilters, (nextFilters) => {
  if (!nextFilters.length) {
    studentDirectoryFilter.value = 'all'
    return
  }

  const hasActiveFilter = nextFilters.some((filter) => filter.value === studentDirectoryFilter.value)
  if (!hasActiveFilter) {
    studentDirectoryFilter.value = 'all'
  }
})

watch(
  [isWorkspaceLoading, workspaceError, activeUnitType, permissionCodes],
  ([loading, error, unitType, nextPermissionCodes]) => {
    const nextCodes = Array.isArray(nextPermissionCodes) ? nextPermissionCodes : []
    const shouldShowAlert = !loading && !error && Boolean(unitType) && nextCodes.length === 0

    if (shouldShowAlert && !hasShownPermissionAlert.value) {
      isPermissionAlertOpen.value = true
      hasShownPermissionAlert.value = true
      return
    }

    if (!shouldShowAlert) {
      isPermissionAlertOpen.value = false
      hasShownPermissionAlert.value = false
    }
  },
  { immediate: true }
)

const isReportMenuOpen = ref(false)
const reportMenuRef = ref(null)
const ssgSummaryCards = computed(() => [
  {
    key: 'total-students',
    label: 'Total Students',
    value: totalStudentsMetric.value.valueLabel,
    icon: GraduationCap,
    tone: 'accent',
    position: 'top-left',
  },
  {
    key: 'students-in-scope',
    label: 'Managed Students',
    value: activeStudentsMetric.value.valueLabel,
    icon: UsersRound,
    tone: 'surface',
    position: 'top-right',
  },
  {
    key: 'events-this-week',
    label: 'Events This Week',
    value: eventVolumeMetric.value.valueLabel,
    icon: CalendarDays,
    tone: 'surface',
    position: 'bottom-left',
  },
  {
    key: 'announcement-reach',
    label: 'Announcement Reach',
    value: latestAnnouncementReachMetric.value.valueLabel,
    icon: BellRing,
    tone: 'accent',
    position: 'bottom-right',
  },
])

const eventHealthGaugeSegments = computed(() => {
  const segmentCount = 15
  const percentage = Number(eventHealthInsight.value?.percentage || 0)
  const activeCount = Math.max(0, Math.min(segmentCount, Math.round((percentage / 100) * segmentCount)))
  const startAngle = 200
  const endAngle = 340
  const radius = 102
  const centerX = 126
  const centerY = 132

  return Array.from({ length: segmentCount }, (_, index) => {
    const ratio = segmentCount > 1 ? index / (segmentCount - 1) : 0
    const angle = startAngle + ((endAngle - startAngle) * ratio)
    const radians = (angle * Math.PI) / 180
    const x = centerX + (Math.cos(radians) * radius)
    const y = centerY + (Math.sin(radians) * radius)

    return {
      key: `event-health-segment-${index}`,
      active: index < activeCount,
      style: {
        left: `${x}px`,
        top: `${y}px`,
        transform: `translate(-50%, -50%) rotate(${angle + 90}deg)`,
        opacity: index < activeCount
          ? `${Math.max(0.45, 1 - (ratio * 0.42))}`
          : '1',
      },
    }
  })
})

function closeReportMenu() {
  isReportMenuOpen.value = false
}

function toggleReportMenu() {
  isReportMenuOpen.value = !isReportMenuOpen.value
}

function handleDocumentPointerDown(event) {
  const menuElement = reportMenuRef.value
  if (menuElement && !menuElement.contains(event.target)) {
    closeReportMenu()
  }

  if (!hasOpenEventSwipe.value) return
  if (event.target.closest('.governance-events__swipe')) return
  closeAllGovernanceEventSwipes()
}

function handleExportPar() {
  closeReportMenu()
  exportPostActivityReport()
}

function handleExportMasterlist() {
  closeReportMenu()
  exportMasterlist()
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})

const createActions = computed(() => {
  const baseActions = [
  {
    key: 'event',
    label: 'Event',
    description: 'Create and publish a governance-scoped event with attendance controls.',
    icon: CalendarDays,
    sectionKey: 'events',
    disabled: !hasPermission('manage_events'),
    disabledReason: 'Needs event permission',
  },
  {
    key: 'announcement',
    label: 'Announcement',
    description: 'Write a new governance update and manage its audience reach.',
    icon: Megaphone,
    sectionKey: 'events',
    disabled: !hasPermission('manage_announcements'),
    disabledReason: 'Needs announcement permission',
  },
  hasPermission('create_sg')
    ? {
      key: 'college-council',
      label: 'College Council',
      description: 'Create an SG and assign it to a department under your SSG.',
      icon: Building2,
      route: props.preview ? '/exposed/governance/create-unit' : '/governance/create-unit',
      disabled: false,
    }
    : null,
  hasPermission('create_org')
    ? {
      key: 'organization',
      label: 'Organization',
      description: 'Create an ORG inside your SG department and prepare its roster.',
      icon: GraduationCap,
      route: props.preview ? '/exposed/governance/create-unit' : '/governance/create-unit',
      disabled: false,
    }
    : null,
  ].filter(Boolean)

  if (isEventsSection.value) {
    return baseActions.filter((action) => ['event', 'announcement'].includes(action.key))
  }

  return baseActions
})

function openAnnouncementDetail(announcement = null) {
  selectedAnnouncement.value = announcement ? { ...announcement } : null
}

function closeAnnouncementDetail() {
  selectedAnnouncement.value = null
}

function openAnnouncementComposer() {
  announcementDraft.value = createAnnouncementDraft()
  announcementComposerError.value = ''
  isAnnouncementComposerOpen.value = true
}

function closeAnnouncementComposer() {
  if (isAnnouncementComposerSaving.value) return
  isAnnouncementComposerOpen.value = false
  announcementComposerError.value = ''
}

function openEventEditor() {
  eventEditorError.value = ''
  editingEvent.value = null
  isEventEditorOpen.value = true
}

function closeEventEditor(force = false) {
  if (isEventEditorSaving.value && !force) return
  isEventEditorOpen.value = false
  eventEditorError.value = ''
  pendingEventCreateRequestKey.value = ''
  editingEvent.value = null
}

function editManagedEvent(event = null) {
  if (!event?.id || !canSwipeEditEvents.value || isEventEditorSaving.value) return
  closeAllGovernanceEventSwipes()
  editingEvent.value = { ...event }
  eventEditorError.value = ''
  isEventEditorOpen.value = true
}

function handleSheetActionSelect(action = null) {
  if (!action || action.disabled) return

  if (isEventsSection.value) {
    closeCreateSheet()

    if (action.key === 'event') {
      openEventEditor()
      return
    }

    if (action.key === 'announcement') {
      openAnnouncementComposer()
      return
    }
  }

  handleCreateAction(action)
}

function resolveNextLocalId(records = []) {
  return Math.max(0, ...records.map((record) => Number(record?.id) || 0)) + 1
}

function replaceEventInLocalFeeds(nextEvent = null) {
  const nextEventId = Number(nextEvent?.id)
  if (!Number.isFinite(nextEventId)) return

  const replaceRecord = (records = []) => {
    let hasMatch = false
    const nextRecords = records.map((record) => {
      if (Number(record?.id) !== nextEventId) return record
      hasMatch = true
      return { ...record, ...nextEvent }
    })
    return hasMatch ? sortEventFeed(nextRecords) : records
  }

  events.value = replaceRecord(events.value)
  campusEvents.value = replaceRecord(campusEvents.value)
}

function getGovernanceEventSwipeOffset(eventId) {
  return Number(eventSwipeOffsets.value[eventId] || 0)
}

function isGovernanceEventSwipeOpen(eventId) {
  return getGovernanceEventSwipeOffset(eventId) > 0
}

function getGovernanceEventSwipeStyle(eventId) {
  return { '--governance-event-swipe-offset': `-${getGovernanceEventSwipeOffset(eventId)}px` }
}

function setGovernanceEventSwipeOffset(eventId, offset) {
  const normalizedOffset = Math.max(0, Math.min(EVENT_SWIPE_ACTION_WIDTH, Number(offset) || 0))
  if (normalizedOffset === 0) {
    if (!Object.keys(eventSwipeOffsets.value).length) return
    eventSwipeOffsets.value = {}
    return
  }

  eventSwipeOffsets.value = { [eventId]: normalizedOffset }
}

function closeAllGovernanceEventSwipes() {
  if (!hasOpenEventSwipe.value) return
  eventSwipeOffsets.value = {}
}

function onGovernanceEventPointerDown(eventId, event) {
  if (!canSwipeEditEvents.value) return
  if (event.pointerType === 'mouse' && event.button !== 0) return
  event.currentTarget.setPointerCapture(event.pointerId)
  eventSwipeDragId.value = eventId
  eventSwipePointerId.value = event.pointerId
  eventSwipeStartX.value = event.clientX
  eventSwipeStartY.value = event.clientY
  eventSwipeStartOffset.value = getGovernanceEventSwipeOffset(eventId)
  eventSwipeAxisLock.value = null
  eventSwipeDidDrag.value = false
}

function onGovernanceEventPointerMove(eventId, event) {
  if (!canSwipeEditEvents.value) return
  if (eventSwipeDragId.value !== eventId || eventSwipePointerId.value !== event.pointerId) return
  const deltaX = event.clientX - eventSwipeStartX.value
  const deltaY = event.clientY - eventSwipeStartY.value

  if (!eventSwipeAxisLock.value) {
    if (Math.abs(deltaX) > EVENT_SWIPE_GESTURE_THRESHOLD || Math.abs(deltaY) > EVENT_SWIPE_GESTURE_THRESHOLD) {
      eventSwipeAxisLock.value = Math.abs(deltaX) > Math.abs(deltaY) ? 'horizontal' : 'vertical'
    }
  }

  if (eventSwipeAxisLock.value === 'horizontal') {
    eventSwipeDidDrag.value = true
    setGovernanceEventSwipeOffset(eventId, eventSwipeStartOffset.value - deltaX)
  }
}

function onGovernanceEventPointerEnd(eventId, event) {
  if (!canSwipeEditEvents.value) return
  if (eventSwipeDragId.value !== eventId || eventSwipePointerId.value !== event.pointerId) return
  eventSwipeDragId.value = null
  eventSwipePointerId.value = null

  if (eventSwipeAxisLock.value === 'horizontal' && eventSwipeDidDrag.value) {
    const currentOffset = getGovernanceEventSwipeOffset(eventId)
    const isOpening = currentOffset > eventSwipeStartOffset.value
    if (isOpening && currentOffset > EVENT_SWIPE_OPEN_THRESHOLD) {
      setGovernanceEventSwipeOffset(eventId, EVENT_SWIPE_ACTION_WIDTH)
    } else if (!isOpening && currentOffset < EVENT_SWIPE_ACTION_WIDTH - EVENT_SWIPE_OPEN_THRESHOLD) {
      setGovernanceEventSwipeOffset(eventId, 0)
    } else {
      setGovernanceEventSwipeOffset(eventId, isOpening ? EVENT_SWIPE_ACTION_WIDTH : 0)
    }
  }

  eventSwipeAxisLock.value = null
}

function onGovernanceEventPointerCancel(eventId, event) {
  if (!canSwipeEditEvents.value) return
  if (eventSwipeDragId.value !== eventId || eventSwipePointerId.value !== event.pointerId) return
  eventSwipeDragId.value = null
  eventSwipePointerId.value = null

  if (eventSwipeStartOffset.value > 0) {
    setGovernanceEventSwipeOffset(eventId, EVENT_SWIPE_ACTION_WIDTH)
  } else {
    setGovernanceEventSwipeOffset(eventId, 0)
  }

  eventSwipeAxisLock.value = null
}

async function handleAnnouncementComposerSave() {
  const title = String(announcementDraft.value.title || '').trim()
  const body = String(announcementDraft.value.body || '').trim()

  if (!title || !body) {
    announcementComposerError.value = 'Title and body are required.'
    return
  }

  const payload = {
    title,
    body,
    status: String(announcementDraft.value.status || 'published').trim().toLowerCase() || 'published',
  }

  if (props.preview) {
    announcements.value = sortAnnouncementFeed([
      {
        id: resolveNextLocalId(announcements.value),
        ...payload,
        created_at: new Date().toISOString(),
      },
      ...announcements.value,
    ])
    closeAnnouncementComposer()
    return
  }

  const activeGovernanceUnitId = Number(activeUnit.value?.id || activeUnit.value?.governance_unit_id)
  if (!Number.isFinite(activeGovernanceUnitId)) {
    announcementComposerError.value = 'The active governance unit is unavailable.'
    return
  }

  isAnnouncementComposerSaving.value = true
  announcementComposerError.value = ''

  try {
    const createdAnnouncement = await createGovernanceAnnouncement(
      apiBaseUrl.value,
      token.value,
      activeGovernanceUnitId,
      payload,
    )

    announcements.value = sortAnnouncementFeed([
      createdAnnouncement || {
        id: resolveNextLocalId(announcements.value),
        ...payload,
        created_at: new Date().toISOString(),
      },
      ...announcements.value,
    ])
    closeAnnouncementComposer()
  } catch (error) {
    announcementComposerError.value = error?.message || 'Unable to publish the announcement.'
  } finally {
    isAnnouncementComposerSaving.value = false
  }
}

function buildScopedEventPayload(payload) {
  const context = normalizeGovernanceContext(activeUnitType.value)
  return {
    payload: {
      ...payload,
      department_ids: normalizeScopeIdList([activeUnit.value?.department_id]),
      program_ids: normalizeScopeIdList([activeUnit.value?.program_id]),
    },
    params: context ? { governance_context: context } : {},
  }
}

function buildScopedEventParams() {
  const context = normalizeGovernanceContext(activeUnitType.value)
  return context ? { governance_context: context } : {}
}

async function handleEventEditorSave(payload) {
  if (isEventEditorSaving.value) return

  const isEditingExistingEvent = Boolean(editingEvent.value?.id)

  if (props.preview) {
    if (isEditingExistingEvent) {
      replaceEventInLocalFeeds({
        ...editingEvent.value,
        ...payload,
      })
    } else {
      events.value = sortEventFeed([
        {
          id: resolveNextLocalId(events.value),
          ...payload,
        },
        ...events.value,
      ])
    }
    closeEventEditor()
    return
  }

  if (!apiBaseUrl.value || !token.value) {
    eventEditorError.value = 'The event service is unavailable right now.'
    return
  }

  isEventEditorSaving.value = true
  eventEditorError.value = ''

  try {
    if (isEditingExistingEvent) {
      const updatedEvent = await updateBackendEvent(
        apiBaseUrl.value,
        token.value,
        editingEvent.value.id,
        payload,
        buildScopedEventParams(),
      )

      replaceEventInLocalFeeds(updatedEvent || {
        ...editingEvent.value,
        ...payload,
      })
    } else {
      if (!pendingEventCreateRequestKey.value) {
        pendingEventCreateRequestKey.value = createIdempotencyKey('governance-event')
      }

      const scopedPayload = buildScopedEventPayload(payload)
      const createdEvent = await createGovernanceEvent(
        apiBaseUrl.value,
        token.value,
        scopedPayload.payload,
        scopedPayload.params,
        {
          headers: {
            'X-Idempotency-Key': pendingEventCreateRequestKey.value,
          },
        }
      )

      closeEventEditor(true)

      events.value = sortEventFeed([
        createdEvent || {
          id: resolveNextLocalId(events.value),
          ...scopedPayload.payload,
        },
        ...events.value,
      ])
      pendingEventCreateRequestKey.value = ''
      return
    }

    closeEventEditor(true)
  } catch (error) {
    pendingEventCreateRequestKey.value = ''
    eventEditorError.value = error?.message || (
      isEditingExistingEvent
        ? 'Unable to save the event changes.'
        : 'Unable to create the event.'
    )
  } finally {
    isEventEditorSaving.value = false
  }
}

function formatAnnouncementAudienceMeta(announcement) {
  const seenCount = Number(
    announcement?.seen_count
    ?? announcement?.seen_students
    ?? announcement?.view_count
    ?? announcement?.read_count
  )
  const audienceCount = Number(
    announcement?.audience_count
    ?? announcement?.target_count
    ?? announcement?.recipient_count
    ?? announcement?.total_recipients
  )

  if (Number.isFinite(seenCount) && Number.isFinite(audienceCount) && audienceCount > 0) {
    return `Seen by ${formatWholeNumber(seenCount)} of ${formatWholeNumber(audienceCount)} students.`
  }
  if (Number.isFinite(seenCount)) {
    return `Seen by ${formatWholeNumber(seenCount)} students.`
  }
  return 'Reach analytics will appear here when the backend provides them.'
}

// ============================================================
// GOVERNANCE ADMIN HUB — Script additions
// ============================================================

/** Readable display labels for backend permission codes (local UI concern only). */
const PERMISSION_LABELS = {
  manage_events: 'Can Manage Events',
  scan_attendance: 'Can Scan Attendance',
  manage_announcements: 'Can Publish Announcements',
  manage_members: 'Can Manage Members',
  assign_permissions: 'Can Assign Permissions',
  create_sg: 'Can Create Councils',
  create_org: 'Can Create Organizations',
  view_reports: 'Can View Reports',
  export_reports: 'Can Export Reports',
}

/** The complete ordered list of permission toggle entries shown in the officer sheet. */
const governancePermissionToggleList = Object.entries(PERMISSION_LABELS)

/** Ref for the officer whose permission sheet is open. */
const governanceSelectedOfficer = ref(null)

/** Whether the current unit is NOT an ORG (ORGs have no child units). */
const governanceShowChildUnits = computed(() => activeUnitType.value !== 'ORG')

/** Section label for the org structure group, adapts per tier. */
const governanceChildUnitsSectionLabel = computed(() => {
  if (activeUnitType.value === 'SSG') return 'College Councils (SGs)'
  if (activeUnitType.value === 'SG') return 'Student Organizations (ORGs)'
  return 'Child Units'
})

/** Child units from active unit detail. Gracefully returns empty if not supplied by backend. */
const governanceChildUnits = computed(() => {
  const rawChildren = activeUnit.value?.child_units
    || activeUnit.value?.children
    || activeUnit.value?.sub_units
    || []
  return Array.isArray(rawChildren) ? rawChildren : []
})

/** Whether the logged-in user can create a child unit. */
const governanceCanAddChildUnit = computed(() =>
  hasPermission('create_sg') || hasPermission('create_org')
)

/** Whether the logged-in user can manage members (used to gate the child-unit manage hint). */
const governanceCanManageMembers = computed(() => hasPermission('manage_members'))

/** Whether the logged-in user can assign permissions to others. */
const governanceCanAssignPermissions = computed(() => hasPermission('assign_permissions'))

const governanceManagedByShortLabel = computed(() => {
  if (activeUnitType.value === 'SSG') return 'Campus Admin'
  if (activeUnitType.value === 'SG') return 'SSG officers'
  if (activeUnitType.value === 'ORG') return 'SG officers'
  return 'Parent governance officers'
})

const governanceManagedByLabel = computed(() => {
  if (activeUnitType.value === 'SSG') return 'Campus Admin manages SSG membership.'
  if (activeUnitType.value === 'SG') return 'SSG manages SG units and SG membership.'
  if (activeUnitType.value === 'ORG') return 'SG manages ORG units and ORG membership.'
  return 'Governance membership follows the parent unit hierarchy.'
})

const governanceManageTargetLabel = computed(() => {
  if (activeUnitType.value === 'SSG') return 'You manage SG child units'
  if (activeUnitType.value === 'SG') return 'You manage ORG child units'
  if (activeUnitType.value === 'ORG') return 'ORG has no lower child tier'
  return 'Child-unit management depends on unit scope'
})

const governanceGuideDescription = computed(() => {
  if (activeUnitType.value === 'SSG') {
    return 'The campus SSG is fixed. Campus Admin owns SSG membership, while SSG officers create and maintain SG child councils.'
  }
  if (activeUnitType.value === 'SG') {
    return 'SG officers manage ORG child units and ORG membership. SG membership itself is controlled by the parent SSG tier.'
  }
  if (activeUnitType.value === 'ORG') {
    return 'ORG is the final governance tier. ORG officers can review their own roster, but SG remains the parent tier that manages ORG membership.'
  }
  return 'This screen separates child-unit structure from officer visibility so the UI stays aligned to backend authority.'
})

const governanceHierarchyCards = computed(() => {
  const currentType = activeUnitType.value
  const base = [
    { key: 'SSG', label: 'Tier 1', title: 'SSG', caption: 'Campus-wide governance' },
    { key: 'SG', label: 'Tier 2', title: 'SG', caption: 'Department councils' },
    { key: 'ORG', label: 'Tier 3', title: 'ORG', caption: 'Program organizations' },
  ]

  return base.map((card) => ({
    ...card,
    tone: resolveGovernanceHierarchyTone(card.key, currentType),
  }))
})

/**
 * Navigate to the member management page for a specific child unit.
 * This is the correct backend flow: an SSG officer with manage_members
 * navigates to /governance/members?unit_id={sg_id} to manage that SG's members.
 * The backend _can_manage_members() will verify the parent-child permission server-side.
 */
function navigateToChildUnitMembers(unit) {
  const unitId = unit?.id || unit?.governance_unit_id
  if (!unitId) {
    console.warn('[GovernanceWorkspaceView] navigateToChildUnitMembers: unit has no id', unit)
    return
  }
  const baseRoute = props.preview ? '/exposed/governance/members' : '/governance/members'
  router.push(`${baseRoute}?unit_id=${unitId}`)
}

function resolveGovernanceHierarchyTone(cardType, currentType) {
  if (!currentType) return 'muted'
  if (cardType === currentType) return 'current'
  if (
    (currentType === 'SG' && cardType === 'SSG')
    || (currentType === 'ORG' && (cardType === 'SSG' || cardType === 'SG'))
  ) {
    return 'upstream'
  }
  if (
    (currentType === 'SSG' && (cardType === 'SG' || cardType === 'ORG'))
    || (currentType === 'SG' && cardType === 'ORG')
  ) {
    return 'downstream'
  }
  return 'muted'
}

/** Helper: generate two-letter initials from a name string. */
function buildOfficerInitials(name = '') {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'OF'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
}

/** Mapped officer rows derived from activeUnit.value?.members array. */
const governanceOfficerRows = computed(() => {
  const rawMembers = activeUnit.value?.members
  if (!Array.isArray(rawMembers) || !rawMembers.length) return []

  return rawMembers.map((member, index) => {
    // Support multiple member payload shapes from the backend
    const user = member?.user || member || {}
    const firstName = user?.first_name || member?.first_name || ''
    const lastName = user?.last_name || member?.last_name || ''
    const name = [firstName, lastName].filter(Boolean).join(' ').trim()
      || user?.email
      || member?.email
      || `Officer ${index + 1}`

    const role = String(
      member?.position
      || member?.role
      || member?.officer_position
      || user?.position
      || ''
    ).trim()

    // Permission codes this member has (may not be returned by all backends)
    const rawPermissions = member?.permissions
      || member?.permission_codes
      || user?.permissions
      || []
    const permissions = Array.isArray(rawPermissions)
      ? rawPermissions.map((p) => String(p?.code || p || '').trim()).filter(Boolean)
      : []

    const numericId = Number(member?.id || user?.id)
    const key = Number.isFinite(numericId) ? numericId : `officer-${index}`

    return {
      key,
      name,
      initials: buildOfficerInitials(name),
      role,
      permissions,
      raw: member,
    }
  })
})

/** Open the permission bottom sheet for a specific officer. */
function openOfficerSheet(officer = null) {
  if (!officer) return
  governanceSelectedOfficer.value = { ...officer }
}

/** Close the officer permission bottom sheet. */
function closeOfficerSheet() {
  governanceSelectedOfficer.value = null
}
</script>

<style scoped>
.governance-workspace {
  --governance-shadow-soft: 0 18px 48px color-mix(in srgb, var(--color-nav) 8%, transparent);
  --governance-shadow-soft-compact: 0 10px 26px color-mix(in srgb, var(--color-nav) 8%, transparent);
  --governance-shadow-strong: 0 18px 48px color-mix(in srgb, var(--color-nav) 14%, transparent);
  --governance-shadow-float: 0 12px 24px color-mix(in srgb, var(--color-nav) 10%, transparent);
  --governance-shadow-popover: 0 18px 44px color-mix(in srgb, var(--color-nav) 14%, transparent);
  --governance-surface-edge: color-mix(in srgb, var(--color-surface) 74%, transparent);
  --governance-surface-edge-strong: color-mix(in srgb, var(--color-surface) 82%, transparent);
  --governance-accent-soft: color-mix(in srgb, var(--color-secondary) 76%, white);
  --governance-warning: var(--color-status-at-risk);
  --governance-warning-bg: color-mix(in srgb, var(--color-status-at-risk) 14%, transparent);
  --governance-danger: var(--color-status-non-compliant);
  --governance-danger-bg: color-mix(in srgb, var(--color-status-non-compliant) 12%, transparent);
  --governance-page-padding: clamp(14px, 4.4vw, 22px);
  --governance-card-padding: clamp(14px, 4vw, 18px);
  --governance-card-radius: clamp(24px, 7vw, 30px);
  min-height: 100vh;
  width: 100%;
  max-width: 100%;
  overflow-x: clip;
  padding: clamp(18px, 5vw, 28px) var(--governance-page-padding) 116px;
  display: flex;
  flex-direction: column;
  gap: clamp(14px, 4vw, 18px);
  font-family: 'Manrope', sans-serif;
  box-sizing: border-box;
}

.governance-workspace--focus {
  padding-top: clamp(10px, 3vw, 16px);
}

.governance-state-card,
.governance-card,
.governance-zone,
.governance-panel,
.governance-empty-card {
  min-width: 0;
  border-radius: var(--governance-card-radius);
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft);
}

.governance-workspace > *,
.governance-top-row > *,
.governance-summary-grid > *,
.governance-analytics-stack > *,
.governance-zone > *,
.governance-events > *,
.governance-events__list > *,
.governance-card__header > *,
.governance-zone__header > *,
.governance-health-card__header-copy,
.governance-events__row-copy {
  min-width: 0;
}

.governance-header__copy {
  gap: 8px;
}

.governance-header__eyebrow,
.governance-card__eyebrow,
.governance-zone__eyebrow,
.governance-panel__eyebrow,
.governance-attention-card__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-header__title,
.governance-zone__title,
.governance-panel__title,
.governance-state-card__title,
.governance-card__title {
  margin: 0;
  font-size: clamp(20px, 6.4vw, 26px);
  line-height: 0.98;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-header__description,
.governance-zone__copy,
.governance-panel__copy,
.governance-state-card__copy,
.governance-card__copy,
.governance-feed-card__body,
.governance-empty-card p,
.governance-placeholder-list__item,
.governance-list__copy span,
.governance-panel__empty {
  margin: 0;
  font-size: clamp(12px, 3.6vw, 14px);
  line-height: 1.65;
  color: var(--color-text-muted);
}

.governance-header__actions {
  gap: 12px;
}

.governance-context-card {
  gap: 6px;
  padding: 18px 20px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 48%),
    color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
}

.governance-context-card__acronym {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-context-card__title {
  font-size: 16px;
  line-height: 1.3;
  color: var(--color-text-primary);
}

.governance-context-card__meta {
  font-size: 13px;
  color: var(--color-text-muted);
}

.governance-create-button,
.governance-inline-action,
.governance-event-card__button {
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

.governance-create-button {
  align-self: center;
  padding: 0 18px;
  height: clamp(52px, 14vw, 56px);
  background: var(--color-primary);
  color: var(--color-banner-text);
  flex-shrink: 0;
  border-radius: 30px;
}

.governance-top-row {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: clamp(8px, 2.8vw, 10px);
  position: relative;
  z-index: 200;
}

.search-wrap {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 100;
}

.search-shell {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  display: grid;
  grid-template-rows: auto 0fr;
  background: var(--color-surface);
  border-radius: 30px;
  padding: 12px clamp(12px, 4vw, 16px);
  box-shadow: var(--governance-shadow-soft-compact);
  min-height: 100%;
  transition: grid-template-rows 0.28s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.28s ease, border-radius 0.28s ease;
}

.search-shell--expanded {
  grid-template-rows: auto 1fr;
  border-radius: 28px;
  box-shadow: var(--governance-shadow-strong);
}

.search-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: clamp(8px, 2.5vw, 10px);
}

.search-results-panel {
  overflow: hidden;
}

.search-results-inner {
  padding-top: 14px;
}

.search-results-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: clamp(240px, 40vh, 360px);
  overflow-y: auto;
  scrollbar-width: thin;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 16px;
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease;
}

.search-result-item:hover,
.search-result-item:focus {
  background: color-mix(in srgb, var(--color-bg) 50%, var(--color-surface));
  outline: none;
}

.search-result-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  flex-shrink: 0;
}

.search-result-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.search-result-copy strong {
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-result-copy span {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-results-empty {
  padding: 20px 0 10px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.search-input {
  width: 100%;
  min-width: 0;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  color: var(--color-text-always-dark);
}

.search-input::placeholder {
  color: var(--color-text-muted);
  font-weight: 500;
}

.search-icon-wrap {
  width: clamp(28px, 8vw, 30px);
  height: clamp(28px, 8vw, 30px);
  border-radius: 50%;
  border: 1.5px solid var(--color-surface-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  place-self: center;
}

.governance-state-card {
  padding: 28px;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.governance-state-card--error {
  color: var(--governance-danger);
}

.governance-state-card__spinner {
  color: var(--color-primary);
  animation: governance-spin 1s linear infinite;
}

.governance-summary-grid {
  display: grid;
  gap: 14px;
}

.governance-summary-grid--ssg {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.governance-analytics-shell,
.governance-analytics-grid,
.governance-analytics-stack,
.governance-health__copy,
.governance-health__metrics {
  display: grid;
  gap: 14px;
}

.governance-analytics-shell__header {
  display: grid;
  gap: 10px;
  padding-inline: 4px;
}

.governance-analytics-shell__title {
  margin: 0;
  font-size: clamp(18px, 5.2vw, 20px);
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-analytics-picker {
  display: grid;
}

.governance-card {
  padding: var(--governance-card-padding);
  gap: clamp(12px, 3.4vw, 14px);
}

.governance-card--health,
.governance-card--chart {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 16%, transparent), transparent 45%),
    color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
}

.governance-card--health-showcase {
  gap: 16px;
  background:
    radial-gradient(circle at 22% 14%, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 32%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 96%, transparent), color-mix(in srgb, var(--color-bg) 40%, var(--color-surface)));
}

.governance-card--engagement {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 44%),
    color-mix(in srgb, var(--color-bg) 44%, var(--color-surface));
}

.governance-card__header,
.governance-zone__header,
.governance-panel__header,
.governance-event-card__top,
.governance-event-card__footer,
.governance-feed-card__top,
.governance-attention-card,
.governance-list__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.governance-card__header--compact {
  align-items: center;
}

.governance-card__status {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
}

.governance-card__engagement-body {
  display: grid;
  gap: 18px;
  place-items: center;
  text-align: center;
}

.governance-health__top,
.governance-health__content,
.governance-health__heading,
.governance-health__stats {
  display: grid;
  gap: 10px;
}

.governance-health__top {
  justify-items: center;
}

.governance-event-select {
  position: relative;
  width: min(100%, 252px);
  justify-self: center;
  display: inline-flex;
  align-items: center;
}

.governance-event-select--primary {
  width: min(100%, 320px);
  justify-self: start;
}

.governance-event-select__input {
  width: 100%;
  min-height: 44px;
  padding: 0 40px 0 16px;
  border: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  outline: none;
  appearance: none;
}

.governance-event-select svg {
  position: absolute;
  right: 14px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.governance-health-card__header,
.governance-health-card__header-copy,
.governance-health-card__tiles {
  display: grid;
  gap: 12px;
}

.governance-health-card__header {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.governance-health-card__menu-wrap {
  position: relative;
}

.governance-health-card__header-copy {
  gap: 6px;
}

.governance-health-card__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.governance-health-card__title {
  margin: 0;
  font-size: clamp(18px, 6vw, 30px);
  line-height: 1.04;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
  overflow-wrap: anywhere;
}

.governance-health-card__menu {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-surface) 86%, transparent);
  color: var(--color-text-muted);
  cursor: pointer;
}

.governance-health-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: clamp(10.5px, 3vw, 12px);
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-health-arc {
  position: relative;
  width: min(100%, clamp(188px, 66vw, 252px));
  height: clamp(156px, 52vw, 196px);
  margin: 0 auto;
}

.governance-health-arc__segment {
  position: absolute;
  width: 14px;
  height: 42px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface));
  transform-origin: center center;
}

.governance-health-arc__segment.is-active {
  background: var(--color-primary);
  box-shadow: 0 10px 24px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.governance-health-arc__center {
  position: absolute;
  left: 50%;
  top: 60%;
  transform: translate(-50%, -50%);
  display: grid;
  justify-items: center;
  gap: 4px;
  text-align: center;
}

.governance-health-arc__value {
  font-size: clamp(20px, 6vw, 24px);
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-health-arc__caption {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-health-arc__badge {
  position: absolute;
  left: clamp(10px, 4vw, 34px);
  top: clamp(30px, 10vw, 44px);
  z-index: 1;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-float);
  color: var(--color-text-primary);
}

.governance-health-arc__badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--color-secondary);
}

.governance-health-arc__badge strong,
.governance-health-arc__badge span {
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
}

.governance-health-arc__badge span:last-child {
  color: var(--color-text-muted);
}

.governance-health-card__tiles {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.governance-health-card__tile {
  min-width: 0;
  padding: 16px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  display: grid;
  gap: 8px;
}

.governance-health-card__tile span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-health-card__tile strong {
  font-size: clamp(24px, 7.8vw, 32px);
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-report-popover {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 10;
  width: min(240px, calc(100vw - 68px));
  padding: 10px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-popover);
  display: grid;
  gap: 8px;
}

.governance-report-popover__action {
  min-height: 46px;
  padding: 0 14px;
  border: none;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  font-size: 13px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

.governance-report-popover__action--primary {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-report-popover__action:disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.governance-health__event-title {
  margin: 0;
  font-size: clamp(20px, 2.5vw, 24px);
  line-height: 1.06;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.governance-health__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-health__state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--color-text-primary);
}

.governance-health__state-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-primary);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.governance-health__body {
  display: grid;
  gap: 18px;
}

.governance-health__body--compact {
  grid-template-columns: minmax(112px, 132px) minmax(0, 1fr);
  align-items: center;
  gap: 16px;
}

.governance-health__stats {
  gap: 0;
}

.governance-health__stat-row {
  min-width: 0;
  padding: 10px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--color-text-muted) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.governance-health__stat-row:last-child {
  border-bottom: none;
}

.governance-health__stat-row span {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-health__stat-row strong {
  font-size: 20px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--color-text-primary);
}

.governance-progress-copy__value {
  font-size: 28px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.governance-progress-copy__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-card--stat {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
}

.governance-card--spotlight {
  min-height: 100%;
}

.governance-card--stat-showcase {
  position: relative;
  overflow: hidden;
  min-height: 160px;
  grid-template-columns: 1fr;
  grid-template-rows: auto 1fr;
  gap: 18px;
  padding: 20px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 96%, transparent), color-mix(in srgb, var(--color-bg) 34%, var(--color-surface)));
  box-shadow:
    0 18px 42px color-mix(in srgb, var(--color-nav) 8%, transparent),
    inset 0 1px 0 var(--governance-surface-edge);
}

.governance-card--stat-showcase-accent {
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-primary) 76%, white),
      color-mix(in srgb, var(--color-primary) 62%, white)
    );
  color: var(--color-banner-text);
  box-shadow:
    0 22px 44px color-mix(in srgb, var(--color-primary) 18%, transparent),
    inset 0 1px 0 color-mix(in srgb, white 56%, transparent);
}

.governance-card--stat-showcase-top-left {
  border-radius: 28px;
}

.governance-card--stat-showcase-top-right {
  border-radius: 28px;
}

.governance-card--stat-showcase-bottom-left {
  border-radius: 28px;
}

.governance-card--stat-showcase-bottom-right {
  border-radius: 28px;
}

.governance-card--stat-showcase-surface {
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-surface) 98%, transparent),
      color-mix(in srgb, var(--color-bg) 32%, var(--color-surface))
    );
  box-shadow:
    inset 0 1px 0 var(--governance-surface-edge-strong),
    0 12px 28px color-mix(in srgb, var(--color-nav) 6%, transparent);
}

.governance-card--stat-showcase > * {
  position: relative;
  z-index: 1;
}

.governance-card--stat-showcase-accent::before {
  content: none;
}

.governance-stat-showcase__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.governance-stat-showcase__eyebrow {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.governance-stat-showcase__eyebrow span {
  min-width: 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  font-size: clamp(10.5px, 3.3vw, 12px);
  line-height: 1.12;
  letter-spacing: -0.02em;
  font-weight: 700;
  color: color-mix(in srgb, var(--color-text-primary) 78%, var(--color-text-muted));
}

.governance-stat-showcase__icon {
  width: 42px;
  height: 42px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-card--stat-showcase-accent .governance-stat-showcase__icon {
  background: color-mix(in srgb, var(--color-banner-text) 12%, transparent);
  color: var(--color-banner-text);
}

.governance-card--stat-showcase-accent .governance-stat-showcase__eyebrow span {
  color: color-mix(in srgb, var(--color-banner-text) 90%, transparent);
}

.governance-stat-showcase__copy {
  min-width: 0;
  display: grid;
  align-content: end;
  gap: 0;
}

.governance-stat-showcase__copy strong {
  font-size: clamp(24px, 8vw, 40px);
  line-height: 0.92;
  letter-spacing: -0.06em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-card--stat-showcase-accent .governance-stat-showcase__copy strong {
  color: var(--color-banner-text);
}

.governance-stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-stat-card__copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.governance-stat-card__copy strong {
  font-size: 28px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-stat-card__copy p {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.governance-feed-card__headline span,
.governance-feed-card__meta,
.governance-event-card__line,
.governance-event-card__time,
.governance-attention-card__copy p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.governance-zone,
.governance-panel {
  padding: var(--governance-card-padding);
  gap: clamp(12px, 3.4vw, 14px);
}

.governance-inline-action {
  padding: 0 14px;
  height: 40px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
}

.governance-attention-list,
.governance-feed-list,
.governance-placeholder-list,
.governance-list,
.governance-chip-list {
  display: grid;
  gap: 12px;
}

.governance-attention-card,
.governance-list__item,
.governance-feed-card {
  width: 100%;
  border: none;
  border-radius: 24px;
  padding: 16px;
  text-align: left;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  color: inherit;
}

.governance-attention-card__icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.governance-attention-card--warning .governance-attention-card__icon {
  background: var(--governance-warning-bg);
  color: var(--governance-warning);
}

.governance-attention-card--critical .governance-attention-card__icon {
  background: var(--governance-danger-bg);
  color: var(--governance-danger);
}

.governance-attention-card--default .governance-attention-card__icon {
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-attention-card__copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.governance-attention-card__copy strong,
.governance-empty-card strong,
.governance-list__copy strong,
.governance-feed-card__headline strong,
.governance-event-card__title {
  font-size: 15px;
  line-height: 1.35;
  color: var(--color-text-primary);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.governance-attention-card__action {
  align-self: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
}

.governance-empty-card {
  padding: 18px;
  gap: 10px;
}

.governance-empty-card--subtle {
  padding: 16px;
  border-radius: 24px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
  box-shadow: none;
}

.governance-empty-card svg {
  color: var(--color-primary);
}

.governance-report-error {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--governance-danger);
}

.governance-report-error--inline {
  padding-inline: 4px;
}

.governance-event-carousel {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(264px, 1fr);
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 4px;
  scroll-snap-type: x proximity;
}

.governance-event-card {
  padding: 16px;
  border-radius: 28px;
  background: color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-snap-align: start;
  min-width: 0;
}

.governance-event-card--live {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 24%, transparent), transparent 46%),
    color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
}

.governance-event-card__status,
.governance-event-card__scope,
.governance-feed-card__status {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.governance-event-card__status,
.governance-feed-card__status {
  color: var(--color-primary);
}

.governance-event-card__scope {
  color: var(--color-text-muted);
}

.governance-event-card__footer {
  align-items: center;
}

.governance-event-card__time {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.governance-event-card__button {
  min-height: 40px;
  padding: 0 14px;
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-feed-card {
  gap: 8px;
}

.governance-events {
  display: grid;
  gap: 16px;
}

.governance-events__header,
.governance-events__section-header,
.governance-live-card__top,
.governance-events__row,
.governance-sheet__header,
.governance-sheet__actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.governance-events__header {
  align-items: center;
}

.governance-events__title {
  margin: 0;
  font-size: clamp(28px, 8.8vw, 48px);
  line-height: 0.92;
  letter-spacing: -0.07em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-events__create-button,
.governance-live-card__scan {
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: inherit;
  font-weight: 800;
  cursor: pointer;
}

.governance-events__create-button {
  width: 52px;
  height: 52px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  box-shadow: var(--governance-shadow-float);
}

.governance-events__toggle {
  padding: 6px;
  border-radius: 999px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft-compact);
}

.governance-events__toggle-button {
  min-height: 44px;
  padding: 0 14px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
}

.governance-events__toggle-button--active {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-live-card {
  padding: 18px;
  border-radius: 30px;
  display: grid;
  gap: 16px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 24%, transparent), transparent 34%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-nav) 92%, var(--color-primary)), color-mix(in srgb, var(--color-nav) 96%, black));
  color: var(--color-nav-text);
  box-shadow: var(--governance-shadow-strong);
}

.governance-live-card__status,
.governance-live-card__scope {
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.governance-live-card__status {
  background: color-mix(in srgb, var(--color-banner-text) 10%, transparent);
  color: var(--color-banner-text);
}

.governance-live-card__scope {
  background: color-mix(in srgb, white 10%, transparent);
  color: color-mix(in srgb, var(--color-nav-text) 88%, transparent);
}

.governance-live-card__pulse {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-primary);
  box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-primary) 38%, transparent);
  animation: governance-live-pulse 1.8s infinite;
}

.governance-live-card__copy,
.governance-sheet__copy,
.governance-sheet__form,
.governance-events__announcements,
.governance-events__list-section {
  display: grid;
  gap: 12px;
}

.governance-live-card__title {
  margin: 0;
  font-size: clamp(28px, 6vw, 40px);
  line-height: 0.96;
  letter-spacing: -0.06em;
  font-weight: 800;
  color: var(--color-nav-text);
}

.governance-live-card__meta {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: color-mix(in srgb, var(--color-nav-text) 72%, transparent);
}

.governance-live-card__scan {
  min-height: 56px;
  padding: 0 18px;
  background: color-mix(in srgb, white 8%, transparent);
  color: var(--color-nav-text);
}

.governance-events__section-title {
  margin: 0;
  font-size: clamp(17px, 5.2vw, 20px);
  line-height: 1;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-events__section-meta {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-events__section-header > div {
  display: grid;
  gap: 4px;
}

.governance-events__calendar-card {
  padding: 18px;
  border-radius: 30px;
  display: grid;
  gap: 16px;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 12%, transparent), transparent 34%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 98%, transparent), color-mix(in srgb, var(--color-bg) 46%, var(--color-surface)));
  box-shadow: var(--governance-shadow-soft);
}

.governance-events__calendar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.governance-events__calendar-eyebrow {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-events__calendar-title {
  margin: 4px 0 0;
  font-size: 24px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-events__calendar-nav {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.governance-events__calendar-nav-button {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-bg) 68%, var(--color-surface));
  color: var(--color-text-primary);
  cursor: pointer;
}

.governance-events__calendar-nav-icon--prev {
  transform: rotate(90deg);
}

.governance-events__calendar-nav-icon--next {
  transform: rotate(-90deg);
}

.governance-events__calendar-weekdays,
.governance-events__calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
}

.governance-events__calendar-weekdays span {
  text-align: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-events__calendar-day {
  min-height: 58px;
  padding: 8px 0 6px;
  border: none;
  border-radius: 18px;
  display: grid;
  justify-items: center;
  align-content: space-between;
  background: color-mix(in srgb, var(--color-bg) 64%, var(--color-surface));
  color: var(--color-text-primary);
  cursor: pointer;
}

.governance-events__calendar-day--outside {
  opacity: 0.42;
}

.governance-events__calendar-day--today {
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-primary) 22%, transparent);
}

.governance-events__calendar-day--selected {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-events__calendar-day--has-events:not(.governance-events__calendar-day--selected) {
  background: color-mix(in srgb, var(--color-primary) 12%, var(--color-surface));
}

.governance-events__calendar-day-number {
  font-size: 14px;
  font-weight: 800;
}

.governance-events__calendar-day-count,
.governance-events__calendar-day-spacer {
  min-width: 20px;
  min-height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
}

.governance-events__calendar-day-count {
  background: color-mix(in srgb, var(--color-primary) 16%, transparent);
  color: var(--color-primary);
}

.governance-events__calendar-day--selected .governance-events__calendar-day-count {
  background: color-mix(in srgb, white 18%, transparent);
  color: var(--color-nav-text);
}

.governance-events__filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.governance-events__filter-pill {
  min-height: 48px;
  padding: 0 14px;
  border: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg) 60%, var(--color-surface));
  color: var(--color-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: var(--governance-shadow-soft-compact);
}

.governance-events__filter-pill strong {
  font-size: 13px;
  font-weight: 800;
  color: inherit;
}

.governance-events__filter-pill--active {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-events__announcement-rail {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(230px, 1fr);
  gap: 12px;
  overflow-x: auto;
  scrollbar-width: none;
}

.governance-events__announcement-rail::-webkit-scrollbar {
  display: none;
}

.governance-events__announcement-card {
  min-height: 170px;
  padding: 16px;
  border: none;
  border-radius: 28px;
  display: grid;
  align-content: start;
  gap: 12px;
  text-align: left;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 14%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 98%, transparent), color-mix(in srgb, var(--color-bg) 38%, var(--color-surface)));
  color: var(--color-text-primary);
  box-shadow: var(--governance-shadow-soft);
  cursor: pointer;
}

.governance-events__announcement-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-events__announcement-title {
  font-size: 18px;
  line-height: 1.08;
  letter-spacing: -0.04em;
  font-weight: 800;
}

.governance-events__announcement-body {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.governance-events__announcement-time {
  margin-top: auto;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-events__list {
  display: grid;
  gap: 12px;
}

.governance-events__swipe {
  position: relative;
  border-radius: 26px;
  overflow: hidden;
}

.governance-events__row-actions {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  align-items: stretch;
  padding: 0 14px;
  border-radius: 26px;
  background: color-mix(in srgb, var(--color-surface) 62%, transparent);
  z-index: 0;
}

.governance-events__row-action {
  width: 68px;
  border: none;
  border-radius: 22px;
  margin: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  font-family: inherit;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}

.governance-events__row-action--edit {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-events__row {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 26px;
  text-align: left;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
  color: var(--color-text-primary);
  box-shadow: var(--governance-shadow-soft-compact);
  display: grid;
  gap: 14px;
  position: relative;
  z-index: 1;
  transform: translateX(var(--governance-event-swipe-offset, 0px));
  transition: transform 180ms ease, box-shadow 180ms ease;
  touch-action: pan-y;
  user-select: none;
  -webkit-user-select: none;
  will-change: transform;
}

.governance-events__row-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.governance-events__row-icon {
  width: 42px;
  height: 42px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-bg) 72%, var(--color-surface));
  color: var(--color-primary);
}

.governance-events__row-copy {
  min-width: 0;
  display: grid;
  gap: 3px;
  flex: 1;
}

.governance-events__row-copy strong {
  font-size: 17px;
  line-height: 1.12;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-events__row-meta {
  font-size: 12px;
  line-height: 1.3;
  font-weight: 600;
  color: var(--color-text-muted);
}

.governance-events__row-state-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 700;
  color: color-mix(in srgb, var(--color-text-muted) 88%, transparent);
}

.governance-events__row-state-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  flex-shrink: 0;
}

.governance-events__row-state-dot--ongoing {
  background: var(--color-primary);
}

.governance-events__row-state-dot--upcoming {
  background: color-mix(in srgb, var(--color-text-muted) 56%, var(--color-primary));
}

.governance-events__row-state-dot--done {
  background: color-mix(in srgb, var(--color-text-muted) 72%, transparent);
}

.governance-events__expand {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-bg) 72%, var(--color-surface));
  color: var(--color-text-primary);
  cursor: pointer;
}

.governance-events__expand-icon--open {
  transform: rotate(180deg);
}

.governance-events__row-details {
  border-top: 1px solid color-mix(in srgb, var(--color-text-muted) 10%, transparent);
  padding-top: 14px;
  display: grid;
  gap: 12px;
}

.governance-events__detail-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.governance-events__detail-metric {
  min-width: 0;
  padding: 12px 14px;
  border-radius: 18px;
  display: grid;
  gap: 6px;
  background: color-mix(in srgb, var(--color-bg) 62%, var(--color-surface));
}

.governance-events__detail-metric span {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.governance-events__detail-metric strong {
  font-size: 28px;
  line-height: 1;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-events__detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.governance-events__detail-button {
  min-height: 34px;
  padding: 0 14px;
  border: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg) 68%, var(--color-surface));
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.governance-events__detail-button--primary {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-events__detail-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.governance-events__detail-error {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 700;
  color: var(--governance-danger);
}

.governance-sheet__backdrop {
  position: fixed;
  inset: 0;
  z-index: 110;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 18px;
  background: color-mix(in srgb, var(--color-nav) 20%, transparent);
  backdrop-filter: blur(14px);
}

.governance-sheet {
  width: min(100%, 560px);
  padding: 22px;
  border-radius: 30px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-strong);
  display: grid;
  gap: 18px;
}

.governance-sheet__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-sheet__title {
  margin: 0;
  font-size: 24px;
  line-height: 1.04;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-sheet__meta,
.governance-sheet__body {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-muted);
}

.governance-sheet__close,
.governance-sheet__secondary,
.governance-sheet__primary {
  border: none;
  font-family: inherit;
  cursor: pointer;
}

.governance-sheet__close {
  width: 42px;
  height: 42px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  color: var(--color-text-primary);
  flex-shrink: 0;
}

.governance-sheet__field {
  display: grid;
  gap: 8px;
}

.governance-sheet__field span {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-sheet__input {
  width: 100%;
  min-height: 48px;
  padding: 12px 16px;
  border: 1px solid color-mix(in srgb, var(--color-nav) 8%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  outline: none;
  box-sizing: border-box;
}

.governance-sheet__input--textarea {
  min-height: 120px;
  resize: vertical;
}

.governance-sheet__error {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--governance-danger);
}

.governance-sheet__secondary,
.governance-sheet__primary {
  min-height: 46px;
  padding: 0 18px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 800;
}

.governance-sheet__secondary {
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
  color: var(--color-text-primary);
}

.governance-sheet__primary {
  background: var(--color-nav);
  color: var(--color-nav-text);
}

.governance-feed-card__top {
  align-items: flex-start;
}

.governance-feed-card__headline {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.governance-feed-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.governance-section-grid {
  display: grid;
  gap: 14px;
}

.governance-panel--primary {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 16%, transparent), transparent 48%),
    color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
}

.governance-placeholder-list__item {
  padding: 12px 14px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-bg) 58%, var(--color-surface));
}

.governance-list__item {
  align-items: center;
}

.governance-list__item--static {
  cursor: default;
}

.governance-list__copy {
  min-width: 0;
  flex: 1;
  gap: 4px;
}

.governance-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.governance-detail-card {
  padding: 14px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--color-bg) 56%, var(--color-surface));
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.governance-detail-card span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.governance-detail-card strong {
  font-size: 16px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-chip-list {
  margin-top: 2px;
}

.governance-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
}

.governance-permission-alert__backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: color-mix(in srgb, var(--color-nav) 22%, transparent);
  backdrop-filter: blur(14px);
}

.governance-permission-alert {
  width: min(100%, 420px);
  padding: 24px;
  border-radius: 30px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: var(--governance-shadow-strong);
  display: grid;
  gap: 18px;
}

.governance-permission-alert__icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--governance-danger-bg);
  color: var(--governance-danger);
}

.governance-permission-alert__copy {
  display: grid;
  gap: 8px;
}

.governance-permission-alert__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--governance-danger);
}

.governance-permission-alert__title {
  margin: 0;
  font-size: 24px;
  line-height: 1.08;
  letter-spacing: -0.05em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.governance-permission-alert__description {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.governance-permission-alert__button {
  min-height: 48px;
  padding: 0 18px;
  border: none;
  border-radius: 18px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 14px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
}

@media (min-width: 768px) {
  .governance-workspace {
    padding: 32px 32px 44px;
    gap: 22px;
  }

  .governance-header {
    grid-template-columns: minmax(0, 1.3fr) auto;
    align-items: flex-end;
  }

  .governance-header__actions {
    align-items: flex-end;
  }

  .governance-create-button {
    align-self: stretch;
  }

  .governance-summary-grid {
    grid-template-columns: minmax(0, 1.15fr) repeat(3, minmax(0, 1fr));
  }

  .governance-summary-grid--ssg {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .governance-health__body {
    grid-template-columns: auto minmax(0, 1fr);
    align-items: center;
  }

  .governance-analytics-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .governance-zone__header {
    align-items: flex-end;
  }

  .governance-section-grid {
    grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  }

  .governance-analytics-shell__header {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: end;
  }

  .governance-events__header {
    align-items: flex-end;
  }

  .governance-events__announcement-rail {
    grid-auto-columns: minmax(270px, 1fr);
  }

  .gov-admin__guide-rail {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .governance-workspace {
    padding-inline: var(--governance-page-padding);
    padding-bottom: calc(112px + env(safe-area-inset-bottom, 0px));
  }

  .governance-header,
  .governance-state-card,
  .governance-card,
  .governance-zone,
  .governance-panel {
    border-radius: 28px;
  }

  .governance-header__title,
  .governance-zone__title,
  .governance-panel__title,
  .governance-state-card__title {
    font-size: 24px;
  }

  .governance-card--stat {
    grid-template-columns: 1fr;
  }

  .governance-card--stat-showcase {
    min-height: clamp(128px, 34vw, 148px);
    gap: clamp(12px, 3.6vw, 16px);
    padding: clamp(14px, 4vw, 16px);
  }

  .governance-summary-grid--ssg {
    gap: 12px;
  }

  .governance-card--stat-showcase-top-left {
    border-radius: 28px;
  }

  .governance-card--stat-showcase-top-right {
    border-radius: 28px;
  }

  .governance-card--stat-showcase-bottom-left {
    border-radius: 28px;
  }

  .governance-card--stat-showcase-bottom-right {
    border-radius: 28px;
  }

  .governance-health-card__title {
    font-size: clamp(18px, 5.8vw, 22px);
  }

  .governance-health-arc {
    width: min(100%, clamp(188px, 64vw, 236px));
    height: clamp(156px, 50vw, 184px);
  }

  .governance-health-arc__badge {
    left: clamp(10px, 4vw, 18px);
    top: clamp(30px, 10vw, 38px);
  }

  .governance-health__body--compact {
    grid-template-columns: minmax(104px, 120px) minmax(0, 1fr);
    align-items: start;
    gap: 14px;
  }

  .governance-health__event-title {
    text-align: left;
  }

  .governance-health__meta {
    justify-content: flex-start;
  }

  .governance-health__content {
    width: 100%;
  }

  .governance-health-card__tiles {
    grid-template-columns: 1fr 1fr;
  }

  .governance-stat-card__icon,
  .governance-stat-showcase__icon {
    width: 42px;
    height: 42px;
  }

  .governance-zone__header,
  .governance-card__header,
  .governance-feed-card__top,
  .governance-attention-card,
  .governance-list__item {
    flex-direction: column;
  }

  .governance-attention-card__action {
    align-self: flex-start;
  }

  .governance-event-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .governance-event-card__button,
  .governance-inline-action {
    width: 100%;
  }

  .governance-permission-alert__backdrop {
    padding: 16px;
  }

  .governance-permission-alert {
    padding: 22px 20px 20px;
    border-radius: 28px;
  }

  .governance-permission-alert__title {
    font-size: 22px;
  }

  .governance-events__title {
    font-size: clamp(28px, 8.8vw, 38px);
  }

  .governance-events__filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .governance-events__detail-actions {
    justify-content: stretch;
  }

  .governance-events__detail-button {
    flex: 1;
  }

  .governance-events__announcement-card {
    min-height: 158px;
  }

  .governance-sheet__backdrop {
    padding: 14px;
  }

  .governance-sheet {
    padding: 20px;
    border-radius: 28px;
  }
}

@media (max-width: 380px) {
  .governance-workspace {
    --governance-page-padding: 12px;
    --governance-card-padding: 13px;
    --governance-card-radius: 24px;
  }

  .governance-top-row {
    gap: 8px;
  }

  .governance-create-button {
    padding-inline: 14px;
  }

  .governance-health-card__menu {
    width: 34px;
    height: 34px;
  }

  .governance-health-card__tiles {
    gap: 10px;
  }
}

.governance-permission-alert-enter-active,
.governance-permission-alert-leave-active {
  transition: opacity 0.24s ease;
}

.governance-permission-alert-enter-active .governance-permission-alert,
.governance-permission-alert-leave-active .governance-permission-alert {
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.24s ease;
}

.governance-permission-alert-enter-from,
.governance-permission-alert-leave-to {
  opacity: 0;
}

.governance-permission-alert-enter-from .governance-permission-alert,
.governance-permission-alert-leave-to .governance-permission-alert {
  transform: translateY(18px) scale(0.98);
  opacity: 0;
}

@keyframes governance-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes governance-live-pulse {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-primary) 42%, transparent);
  }
  70% {
    box-shadow: 0 0 0 12px color-mix(in srgb, var(--color-primary) 0%, transparent);
  }
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-primary) 0%, transparent);
  }
}

.governance-directory {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 10px;
}

.governance-directory__filters {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}

.governance-directory__filters::-webkit-scrollbar {
  display: none;
}

.governance-directory__filter {
  padding: 8px 16px;
  border-radius: 20px;
  background-color: color-mix(in srgb, var(--color-surface) 60%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.governance-directory__filter:hover {
  background-color: var(--color-surface);
  color: var(--color-text);
  border-color: color-mix(in srgb, var(--color-border) 80%, transparent);
}

.governance-directory__filter--active {
  background-color: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  border-color: transparent;
}

.governance-directory__list {
  display: flex;
  flex-direction: column;
}

.governance-directory__item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
}

.governance-directory__item:last-child {
  border-bottom: none;
}

.governance-directory__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background-color: color-mix(in srgb, var(--color-primary) 8%, transparent);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.governance-directory__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.governance-directory__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.governance-directory__meta {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.governance-directory__status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  max-width: 124px;
  padding: 8px 12px;
  border-radius: 999px;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}

.governance-directory__status--present {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.governance-directory__status--late {
  background: rgba(249, 115, 22, 0.14);
  color: #c2410c;
}

.governance-directory__status--waiting {
  background: rgba(59, 130, 246, 0.14);
  color: #1d4ed8;
}

.governance-directory__status--absent {
  background: rgba(239, 68, 68, 0.14);
  color: #b91c1c;
}

.governance-directory__status--excused {
  background: rgba(168, 85, 247, 0.14);
  color: #7e22ce;
}

.governance-directory__status--neutral {
  background: rgba(100, 116, 139, 0.14);
  color: #475569;
}

.governance-student-directory {
  display: grid;
  gap: 16px;
}

.governance-student-directory__search-shell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 52px;
  padding: 0 16px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg) 48%, var(--color-surface));
  color: var(--color-text-muted);
  box-shadow: var(--governance-shadow-soft-compact);
}

.governance-student-directory__search-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
  font-size: 14px;
  font-weight: 600;
}

.governance-student-directory__search-input::placeholder {
  color: var(--color-text-muted);
}

.governance-student-directory__list {
  border-radius: 28px;
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft);
  padding: 4px 18px;
}

.governance-student-directory__avatar {
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent 48%),
    color-mix(in srgb, var(--color-bg) 52%, var(--color-surface));
}

.governance-student-directory__avatar-text {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--color-primary);
}

.governance-events__attendance {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}

.governance-events__attendance-eyebrow {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin: 0 0 10px 0;
}

.governance-list--compact {
  gap: 6px;
}

.governance-list--compact .governance-list__item {
  padding: 8px 12px;
  border-radius: 12px;
  background-color: color-mix(in srgb, var(--color-surface) 60%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
}

.governance-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.governance-badge--present {
  background-color: color-mix(in srgb, #10b981 12%, transparent);
  color: #059669;
}

.governance-badge--late {
  background-color: color-mix(in srgb, #f59e0b 12%, transparent);
  color: #d97706;
}

.governance-badge--absent {
  background-color: color-mix(in srgb, #ef4444 12%, transparent);
  color: #dc2626;
}

.governance-badge--waiting {
  background-color: color-mix(in srgb, var(--color-text-muted) 12%, transparent);
  color: var(--color-text-muted);
}

/* ============================================================
   GOVERNANCE ADMIN HUB — Apple HIG Inset Grouped List
   ============================================================ */

.gov-admin {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Header */
.gov-admin__header {
  padding: 4px 4px 20px;
}

.gov-admin__title {
  margin: 0;
  font-size: clamp(30px, 9vw, 38px);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1;
  color: var(--color-text-primary);
}

.gov-admin__subtitle {
  margin: 10px 0 0;
  max-width: 56ch;
  font-size: 13px;
  line-height: 1.6;
  font-weight: 600;
  color: var(--color-text-muted);
}

/* Identity Card (Group 1) */
.gov-admin__identity-card {
  border-radius: var(--governance-card-radius);
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 22%, transparent), transparent 52%),
    color-mix(in srgb, var(--color-bg) 44%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft);
  padding: clamp(16px, 4.5vw, 20px) clamp(16px, 4.5vw, 20px);
  margin-bottom: 24px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.gov-admin__identity-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}

.gov-admin__identity-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--color-primary) 16%, transparent);
  color: var(--color-primary);
  flex-shrink: 0;
}

.gov-admin__identity-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.gov-admin__identity-name {
  font-size: clamp(15px, 4.2vw, 17px);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gov-admin__identity-meta {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.gov-admin__identity-badge {
  flex-shrink: 0;
  padding: 5px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.gov-admin__guide-card {
  border-radius: var(--governance-card-radius);
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 14%, transparent), transparent 38%),
    color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft);
  padding: clamp(16px, 4.5vw, 20px);
  display: grid;
  gap: 16px;
  margin-bottom: 24px;
}

.gov-admin__guide-copy {
  display: grid;
  gap: 8px;
}

.gov-admin__guide-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 24px);
  line-height: 1.08;
  letter-spacing: -0.04em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.gov-admin__guide-description,
.gov-admin__guide-step-copy {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.gov-admin__guide-rail {
  display: grid;
  gap: 10px;
}

.gov-admin__guide-step {
  border-radius: 20px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--color-border) 48%, transparent);
  background: rgba(255, 255, 255, 0.82);
  display: grid;
  gap: 8px;
}

.gov-admin__guide-step--current {
  border-color: color-mix(in srgb, var(--color-primary) 28%, transparent);
  background: color-mix(in srgb, var(--color-primary) 10%, rgba(255, 255, 255, 0.96));
}

.gov-admin__guide-step--upstream {
  background: rgba(241, 245, 249, 0.9);
}

.gov-admin__guide-step-tag {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.gov-admin__guide-step-title {
  font-size: 15px;
  line-height: 1.2;
  letter-spacing: -0.03em;
  font-weight: 800;
  color: var(--color-text-primary);
}

.gov-admin__guide-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.gov-admin__guide-pill {
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.gov-admin__guide-pill--muted {
  background: color-mix(in srgb, var(--color-text-muted) 10%, transparent);
  color: var(--color-text-secondary);
}

/* Section Labels (above each group card) */
.gov-admin__section-label {
  margin: 0 0 8px 4px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.gov-admin__section-label--flush {
  margin: 0;
}

/* Group Card */
.gov-admin__group {
  border-radius: var(--governance-card-radius);
  background: color-mix(in srgb, var(--color-bg) 46%, var(--color-surface));
  box-shadow: var(--governance-shadow-soft);
  overflow: hidden;
  margin-bottom: 24px;
}

.gov-admin__group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px clamp(14px, 4vw, 18px) 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 60%, transparent);
}

.gov-admin__group-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.gov-admin__add-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 999px;
  border: none;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.1s ease;
}

.gov-admin__add-button:hover,
.gov-admin__add-button:focus {
  background: color-mix(in srgb, var(--color-primary) 22%, transparent);
  outline: none;
  transform: scale(1.03);
}

.gov-admin__add-button:active {
  transform: scale(0.97);
}

/* List Row */
.gov-admin__row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px clamp(14px, 4vw, 18px);
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  text-align: left;
  width: 100%;
  background: transparent;
  border-left: none;
  border-right: none;
  border-top: none;
  font-family: inherit;
}

.gov-admin__row--last {
  border-bottom: none;
}

.gov-admin__row--button {
  cursor: pointer;
  transition: background 0.15s ease;
}

.gov-admin__row--button:hover,
.gov-admin__row--button:focus {
  background: color-mix(in srgb, var(--color-primary) 5%, transparent);
  outline: none;
}

.gov-admin__row--button:active {
  background: color-mix(in srgb, var(--color-primary) 9%, transparent);
}

.gov-admin__row-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--color-text-muted) 10%, transparent);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.gov-admin__row-icon--permission {
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
}

.gov-admin__row-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.gov-admin__row-copy strong {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gov-admin__row-copy span {
  font-size: 12px;
  color: var(--color-text-muted);
}

.gov-admin__row-chevron {
  flex-shrink: 0;
  color: var(--color-text-muted);
  opacity: 0.5;
  transform: rotate(-90deg);
}

/* Manage hint pill shown on child unit rows */
.gov-admin__row-manage-hint {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.gov-admin__row-manage-hint span {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  padding: 3px 9px;
  border-radius: 20px;
}

/* Officer Avatar */
.gov-admin__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  flex-shrink: 0;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 20%, transparent), transparent 60%),
    color-mix(in srgb, var(--color-bg) 50%, var(--color-surface));
}

.gov-admin__avatar--large {
  width: 48px;
  height: 48px;
}

.gov-admin__avatar-text {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--color-primary);
}

.gov-admin__avatar--large .gov-admin__avatar-text {
  font-size: 15px;
}

/* Empty state inside a group */
.gov-admin__group-empty {
  padding: 18px clamp(14px, 4vw, 18px);
  display: flex;
  align-items: center;
}

.gov-admin__group-empty span {
  font-size: 13px;
  color: var(--color-text-muted);
  font-weight: 500;
  font-style: italic;
}

/* ---- Permission Bottom Sheet ---- */

.gov-admin__sheet-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 9000;
  display: flex;
  align-items: flex-end;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.gov-admin__sheet {
  width: 100%;
  max-height: 82dvh;
  overflow-y: auto;
  border-radius: 28px 28px 0 0;
  background: var(--color-surface);
  box-shadow: 0 -24px 60px rgba(0, 0, 0, 0.24);
  display: flex;
  flex-direction: column;
  scrollbar-width: none;
}

.gov-admin__sheet::-webkit-scrollbar {
  display: none;
}

.gov-admin__sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 20px 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 50%, transparent);
  gap: 12px;
}

.gov-admin__sheet-identity {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.gov-admin__sheet-name {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
}

.gov-admin__sheet-role {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.gov-admin__sheet-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-text-muted) 10%, transparent);
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s ease;
}

.gov-admin__sheet-close:hover {
  background: color-mix(in srgb, var(--color-text-muted) 18%, transparent);
}

.gov-admin__sheet-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: color-mix(in srgb, var(--color-text-muted) 8%, transparent);
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 50%, transparent);
}

.gov-admin__sheet-notice strong {
  color: var(--color-text-primary);
}

.gov-admin__sheet-toggles {
  display: flex;
  flex-direction: column;
  padding: 6px 0 24px;
}

.gov-admin__permission-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 36%, transparent);
}

.gov-admin__permission-row:last-child {
  border-bottom: none;
}

.gov-admin__permission-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.gov-admin__permission-copy strong {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.gov-admin__permission-copy span {
  font-size: 11px;
  color: var(--color-text-muted);
  letter-spacing: 0.02em;
}

/* iOS-style Toggle Switch */
.gov-admin__toggle {
  flex-shrink: 0;
  position: relative;
  width: 48px;
  height: 28px;
  border-radius: 999px;
  border: none;
  background: color-mix(in srgb, var(--color-text-muted) 22%, transparent);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
}

.gov-admin__toggle--on {
  background: var(--color-primary);
}

.gov-admin__toggle:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.gov-admin__toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.22);
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  display: block;
}

.gov-admin__toggle--on .gov-admin__toggle-knob {
  transform: translateX(20px);
}

/* Bottom Sheet Transition */
.gov-sheet-enter-active,
.gov-sheet-leave-active {
  transition: opacity 0.28s ease;
}

.gov-sheet-enter-active .gov-admin__sheet,
.gov-sheet-leave-active .gov-admin__sheet {
  transition: transform 0.32s cubic-bezier(0.4, 0, 0.2, 1);
}

.gov-sheet-enter-from,
.gov-sheet-leave-to {
  opacity: 0;
}

.gov-sheet-enter-from .gov-admin__sheet,
.gov-sheet-leave-to .gov-admin__sheet {
  transform: translateY(100%);
}
</style>
