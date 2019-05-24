#pragma once

#include <QtWidgets/QWidget>
#include <QtGui/QImage>
#include <thread>
#include <mutex>
#include "uitypes.h"


class EntropyThread
{
	BinaryViewRef m_data;
	QImage* m_image;
	size_t m_blockSize;
	bool m_updated, m_running;
	std::thread m_thread;
	std::mutex m_mutex;

public:
	EntropyThread(BinaryViewRef data, int width, size_t blockSize, QImage* image);
	~EntropyThread();

	void Run();
	bool IsUpdated() { return m_updated; }
	void ResetUpdated() { m_updated = false; }

	void Lock();
	void Unlock();
};


class TriageView;

class EntropyWidget: public QWidget
{
	TriageView* m_view;
	BinaryViewRef m_data, m_rawData;
	size_t m_blockSize;
	int m_width;
	QImage m_image;
	EntropyThread* m_thread;

public:
	EntropyWidget(QWidget* parent, TriageView* view, BinaryViewRef data);
	virtual ~EntropyWidget();

	virtual QSize sizeHint() const override;

protected:
	virtual void paintEvent(QPaintEvent* event) override;
	virtual void mousePressEvent(QMouseEvent* event) override;

private Q_SLOTS:
	void timerExpired();
};
